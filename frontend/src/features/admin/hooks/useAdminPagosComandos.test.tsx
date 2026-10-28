// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  construirPayloadAnularManual,
  construirPayloadAprobarManual,
  invalidarLecturasPago,
  useAprobarPagoManual,
} from "./useAdminPagosComandos";

/**
 * The mutations of the payments.
 *
 * The suite verifies the three contracts that the dialog and the table
 * depend on:
 *
 * 1. the EXACT payload that travels to the API (the channel, the reference,
 *    the amount as a NUMBER, the currency and the motive),
 * 2. the Zod mirrors that validate that payload BEFORE it leaves the
 *    browser,
 * 3. the EXACT keys of the reads that every write invalidates.
 */

const { aprobarPagoManual } = vi.hoisted(() => ({
  aprobarPagoManual: vi.fn(),
}));

vi.mock("../services/admin.pago.service", () => ({
  anularPagoManual: vi.fn(),
  aprobarPagoManual,
  getAdminPagoDetalle: vi.fn(),
  getAdminPagos: vi.fn(),
}));

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

describe("Los payloads de la aprobación manual", () => {
  it("compone el cuerpo EXACTO de la aprobación", () => {
    const payload = construirPayloadAprobarManual({
      canal: "YAPE",
      referencia: "  OP-999  ",
      monto: "400.00",
      moneda: "pen",
      motivo: "  Abono verificado  ",
    });

    expect(payload).toEqual({
      canal: "YAPE",
      referencia: "OP-999",
      monto: 400,
      moneda: "PEN",
      motivo: "Abono verificado",
    });
  });

  it("compone el cuerpo EXACTO de la anulación", () => {
    const payload = construirPayloadAnularManual({
      motivo: "  Registro duplicado  ",
    });

    expect(payload).toEqual({ motivo: "Registro duplicado" });
  });
});

describe("Los mirrors Zod de la aprobación manual", () => {
  it("acepta el cuerpo que envía el hook", async () => {
    const { AdminPagoAprobarManualPayloadSchema } = await import("../schemas");

    const payload = construirPayloadAprobarManual({
      canal: "TRANSFERENCIA_BANCARIA",
      referencia: "OP-1",
      monto: "400.00",
      moneda: "PEN",
      motivo: "Abono verificado",
    });

    expect(AdminPagoAprobarManualPayloadSchema.safeParse(payload).success).toBe(
      true,
    );
  });

  it("RECHAZA un canal que no pertenece al conjunto cerrado", async () => {
    const { AdminPagoAprobarManualPayloadSchema } = await import("../schemas");

    const resultado = AdminPagoAprobarManualPayloadSchema.safeParse({
      canal: "CRIPTO",
      referencia: "OP-1",
      monto: 400,
      moneda: "PEN",
      motivo: "Abono verificado",
    });

    expect(resultado.success).toBe(false);
  });

  it("RECHAZA una referencia vacía y un monto no numérico", async () => {
    const { AdminPagoAprobarManualFormSchema } = await import("../schemas");

    expect(
      AdminPagoAprobarManualFormSchema.safeParse({
        canal: "EFECTIVO",
        referencia: "   ",
        monto: "cuatrocientos",
        moneda: "PEN",
        motivo: "Abono verificado",
      }).success,
    ).toBe(false);
  });
});

describe("La invalidación de las lecturas del pago", () => {
  it("invalida la lista, el detalle y el resumen", async () => {
    const cliente = crearCliente();
    const invalidas: unknown[] = [];
    cliente.invalidateQueries = vi.fn((filtro: unknown) => {
      invalidas.push(filtro);
      return Promise.resolve();
    }) as typeof cliente.invalidateQueries;

    await invalidarLecturasPago(cliente, ORDEN_PAGO_ID);

    expect(invalidas).toEqual([
      { queryKey: ["admin", "pagos"], exact: false },
      { queryKey: ["admin", "pago", ORDEN_PAGO_ID], exact: true },
      { queryKey: ["admin", "resumen"], exact: true },
    ]);
  });
});

describe("La mutación de aprobación manual", () => {
  it("viaja con el payload construido por el hook", async () => {
    aprobarPagoManual.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });

    const cliente = crearCliente();
    const { result } = renderHook(() => useAprobarPagoManual(), {
      wrapper: envoltorio(cliente),
    });

    await result.current.mutateAsync({
      ordenPagoId: ORDEN_PAGO_ID,
      datos: {
        canal: "EFECTIVO",
        referencia: "OP-77",
        monto: "400.00",
        moneda: "PEN",
        motivo: "Pago en caja",
      },
    });

    expect(aprobarPagoManual).toHaveBeenCalledTimes(1);
    expect(aprobarPagoManual).toHaveBeenCalledWith(ORDEN_PAGO_ID, {
      canal: "EFECTIVO",
      referencia: "OP-77",
      monto: 400,
      moneda: "PEN",
      motivo: "Pago en caja",
    });
  });
});
