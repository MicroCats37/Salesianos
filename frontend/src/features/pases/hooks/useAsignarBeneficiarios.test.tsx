// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  construirPayloadAsignarBeneficiarios,
  invalidarLecturasBeneficiarios,
  useAsignarBeneficiarios,
} from "./useAsignarBeneficiarios";
import {
  construirPayloadRevocarBeneficiario,
  useRevocarBeneficiario,
} from "./useRevocarBeneficiario";

/**
 * The mutations of the nominative rights of a pass.
 *
 * The suite verifies the three contracts the buyer panel depends on:
 *
 * 1. the EXACT payload that travels to the API (ONLY the ids of the persons
 *    that already exist),
 * 2. the Zod mirrors that validate that payload BEFORE it leaves the browser,
 * 3. the EXACT keys of the reads that every write invalidates (the rights of
 *    the batch AND the commercial state of the purchase).
 */

const { asignarBeneficiariosCompra, revocarBeneficiarioCompra } = vi.hoisted(
  () => ({
    asignarBeneficiariosCompra: vi.fn(),
    revocarBeneficiarioCompra: vi.fn(),
  }),
);

vi.mock("../services/pase.beneficiario.service", () => ({
  asignarBeneficiariosCompra,
  fetchBeneficiariosCompra: vi.fn(),
  revocarBeneficiarioCompra,
}));

const COMPRA_ID = "22222222-2222-4222-8222-222222222222";
const PERSONA_ID = "33333333-3333-4333-8333-333333333333";

const PERSONA = {
  persona_id: PERSONA_ID,
  nombre_completo: "Ana Pérez",
  tipo_documento: "DNI",
  numero_documento: "12345678",
};

function crearCliente() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function envoltorio(cliente: QueryClient) {
  return function Envoltorio({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={cliente}>{children}</QueryClientProvider>
    );
  };
}

describe("Los payloads de los beneficiarios", () => {
  it("el cuerpo de la asignación lleva SOLO los ids", () => {
    const payload = construirPayloadAsignarBeneficiarios([
      PERSONA,
      {
        persona_id: "44444444-4444-4444-8444-444444444444",
        nombre_completo: "Luis Quispe",
        tipo_documento: "CE",
        numero_documento: "12345678",
      },
    ]);

    expect(payload).toEqual({
      beneficiario_ids: [PERSONA_ID, "44444444-4444-4444-8444-444444444444"],
    });
  });

  it("el cuerpo de la revocación lleva el motivo limpio", () => {
    expect(
      construirPayloadRevocarBeneficiario("  Error de asignación  "),
    ).toEqual({ motivo: "Error de asignación" });
  });
});

describe("Los mirrors Zod de los beneficiarios", () => {
  it("acepta el cuerpo que envía el hook", async () => {
    const { paseBeneficiariosAsignarInSchema } = await import("../schemas");

    const payload = construirPayloadAsignarBeneficiarios([PERSONA]);

    expect(paseBeneficiariosAsignarInSchema.safeParse(payload).success).toBe(
      true,
    );
  });

  it("RECHAZA una asignación sin personas", async () => {
    const { paseBeneficiariosAsignarInSchema } = await import("../schemas");

    expect(
      paseBeneficiariosAsignarInSchema.safeParse({
        beneficiario_ids: [],
      }).success,
    ).toBe(false);
  });

  it("RECHAZA una revocación sin motivo", async () => {
    const { paseBeneficiarioRevocarInSchema } = await import("../schemas");

    expect(
      paseBeneficiarioRevocarInSchema.safeParse({ motivo: "   " }).success,
    ).toBe(false);
  });
});

describe("La invalidación de las lecturas de los beneficiarios", () => {
  it("invalida los derechos del lote Y el estado de la compra", async () => {
    const cliente = crearCliente();
    const invalidas: unknown[] = [];
    cliente.invalidateQueries = vi.fn((filtro: unknown) => {
      invalidas.push(filtro);
      return Promise.resolve();
    }) as typeof cliente.invalidateQueries;

    await invalidarLecturasBeneficiarios(cliente, COMPRA_ID);

    expect(invalidas).toEqual([
      { queryKey: ["pases", "beneficiarios", COMPRA_ID], exact: true },
      { queryKey: ["pases", "compra", COMPRA_ID], exact: true },
    ]);
  });
});

describe("La mutación de asignación", () => {
  it("viaja con el payload construido por el hook", async () => {
    asignarBeneficiariosCompra.mockResolvedValue({
      compra_id: COMPRA_ID,
      cantidad_pases: 2,
      activos: 2,
      revocados: 0,
      slots_usados: 2,
      slots_disponibles: 0,
      asignados: 2,
      ya_asignados: 0,
      beneficiarios: [],
    });

    const cliente = crearCliente();
    const { result } = renderHook(() => useAsignarBeneficiarios(), {
      wrapper: envoltorio(cliente),
    });

    await result.current.mutateAsync({
      compraId: COMPRA_ID,
      personas: [PERSONA],
    });

    expect(asignarBeneficiariosCompra).toHaveBeenCalledTimes(1);
    expect(asignarBeneficiariosCompra).toHaveBeenCalledWith(COMPRA_ID, [
      PERSONA_ID,
    ]);
  });
});

describe("La mutación de revocación", () => {
  it("viaja con el motivo auditado", async () => {
    revocarBeneficiarioCompra.mockResolvedValue({
      compra_id: COMPRA_ID,
      cantidad_pases: 2,
      activos: 1,
      revocados: 1,
      slots_usados: 2,
      slots_disponibles: 0,
      persona_id: PERSONA_ID,
      estado: "REVOCADA",
      revocado_en: "2026-10-29T10:00:00",
      ya_revocado: false,
    });

    const cliente = crearCliente();
    const { result } = renderHook(() => useRevocarBeneficiario(), {
      wrapper: envoltorio(cliente),
    });

    await result.current.mutateAsync({
      compraId: COMPRA_ID,
      personaId: PERSONA_ID,
      motivo: "Error de asignación",
    });

    expect(revocarBeneficiarioCompra).toHaveBeenCalledTimes(1);
    expect(revocarBeneficiarioCompra).toHaveBeenCalledWith(
      COMPRA_ID,
      PERSONA_ID,
      "Error de asignación",
    );
  });
});
