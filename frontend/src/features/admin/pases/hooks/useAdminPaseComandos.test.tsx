// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  construirPayloadCancelarCompraPase,
  invalidarLecturasPase,
  useCancelarCompraPase,
} from "./useAdminPaseComandos";

/**
 * The administrative cancellation of a pass purchase.
 *
 * The suite verifies the three contracts the dialog and the payments table
 * depend on:
 *
 * 1. the EXACT payload that travels to the API (the audited motive),
 * 2. the Zod mirror that validates that payload BEFORE it leaves the browser,
 * 3. the EXACT keys of the reads that the cancellation invalidates: the
 *    payments table, the drilldown of the order, the overview and the state of
 *    the purchase (the buyer sees the cancelled batch).
 */

const { cancelarCompraPase } = vi.hoisted(() => ({
  cancelarCompraPase: vi.fn(),
}));

vi.mock("../services/admin.pase.service", () => ({
  cancelarCompraPase,
}));

const COMPRA_ID = "22222222-2222-4222-8222-222222222222";
const ORDEN_PAGO_ID = "11111111-1111-4111-8111-111111111111";

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

describe("El payload de la cancelación administrativa", () => {
  it("compone el cuerpo EXACTO con el motivo limpio", () => {
    expect(
      construirPayloadCancelarCompraPase("  Solicitud del comprador  "),
    ).toEqual({ motivo: "Solicitud del comprador" });
  });

  it("RECHAZA un motivo vacío", async () => {
    const { AdminPaseCancelarFormSchema, AdminPaseCancelarPayloadSchema } =
      await import("../schemas");

    // The FORM rejects the blank motive (it trims before validating).
    expect(
      AdminPaseCancelarFormSchema.safeParse({ motivo: "   " }).success,
    ).toBe(false);

    // And the payload builder TRIMS it, so the payload mirror refuses it too.
    const payload = construirPayloadCancelarCompraPase("   ");
    expect(payload).toEqual({ motivo: "" });
    expect(AdminPaseCancelarPayloadSchema.safeParse(payload).success).toBe(
      false,
    );
  });
});

describe("La invalidación de las lecturas de la cancelación", () => {
  it("invalida la tabla, el detalle, el resumen y el estado de la compra", async () => {
    const cliente = crearCliente();
    const invalidas: unknown[] = [];
    cliente.invalidateQueries = vi.fn((filtro: unknown) => {
      invalidas.push(filtro);
      return Promise.resolve();
    }) as typeof cliente.invalidateQueries;

    await invalidarLecturasPase(cliente, {
      compraId: COMPRA_ID,
      ordenPagoId: ORDEN_PAGO_ID,
      motivo: "Solicitud del comprador",
    });

    expect(invalidas).toEqual([
      { queryKey: ["admin", "pagos"], exact: false },
      { queryKey: ["admin", "resumen"], exact: true },
      { queryKey: ["admin", "pago", ORDEN_PAGO_ID], exact: true },
      { queryKey: ["pases", "compra", COMPRA_ID], exact: true },
      { queryKey: ["pases", "beneficiarios", COMPRA_ID], exact: true },
    ]);
  });

  it("una compra SIN orden de pago no invalida un detalle inexistente", async () => {
    const cliente = crearCliente();
    const invalidas: unknown[] = [];
    cliente.invalidateQueries = vi.fn((filtro: unknown) => {
      invalidas.push(filtro);
      return Promise.resolve();
    }) as typeof cliente.invalidateQueries;

    await invalidarLecturasPase(cliente, {
      compraId: COMPRA_ID,
      ordenPagoId: null,
      motivo: "Solicitud del comprador",
    });

    expect(invalidas).toHaveLength(4);
    expect(invalidas).not.toContainEqual({
      queryKey: ["admin", "pago", null],
      exact: true,
    });
  });
});

describe("La mutación de cancelación administrativa", () => {
  it("viaja con el payload construido por el hook", async () => {
    cancelarCompraPase.mockResolvedValue({
      compra_id: COMPRA_ID,
      estado_compra: "CANCELADA",
      estado_orden: "CANCELADA",
      ya_cancelada: false,
      beneficiarios_revocados: 2,
      personas_afectadas: 2,
      motivo: "Solicitud del comprador",
    });

    const cliente = crearCliente();
    const { result } = renderHook(() => useCancelarCompraPase(), {
      wrapper: envoltorio(cliente),
    });

    await result.current.mutateAsync({
      compraId: COMPRA_ID,
      ordenPagoId: ORDEN_PAGO_ID,
      motivo: "Solicitud del comprador",
    });

    expect(cancelarCompraPase).toHaveBeenCalledTimes(1);
    expect(cancelarCompraPase).toHaveBeenCalledWith(COMPRA_ID, {
      motivo: "Solicitud del comprador",
    });
  });
});
