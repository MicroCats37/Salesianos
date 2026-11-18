import { describe, expect, it, vi } from "vitest";
import type { TransaccionEstadoResponse } from "../schemas/pago.schema";
import {
  esEstadoExito,
  INTERVALO_SONDEO_MS,
  MAX_SONDEOS,
  sondearEstadoTransaccion,
} from "./checkout.recuperacion";

/**
 * The recovery of an uncertain relay.
 *
 * The suite verifies the CONTRACT of the bounded polling:
 *
 * 1. it detects the recorded success of the transaction it prepared,
 * 2. it reports a definitive rejection instead of waiting for it,
 * 3. it NEVER exceeds its bound,
 * 4. a failed read is not a failed payment,
 * 5. it stops when the checkout is closed.
 */

const TRANSACCION_ID = "12345678901234";

function transaccion(
  status: "PENDIENTE" | "EXITO" | "FALLIDO" | "CANCELADO",
  responseMessage: string | null = null,
): TransaccionEstadoResponse {
  return {
    success: true,
    data: {
      id: "t-1",
      orden_pago_id: "o-1",
      transaction_id: TRANSACCION_ID,
      order_number: "1234567890",
      amount: 400,
      currency: "PEN",
      status,
      response_code: status === "EXITO" ? "00" : null,
      response_message: responseMessage,
      metodo_pago: status === "EXITO" ? "CARD" : null,
      created_at: "2026-01-01T00:00:00",
      updated_at: "2026-01-01T00:00:00",
    },
    message: "Transaccion encontrada.",
  };
}

/** A wait that never touches the clock of the test. */
const dormirInstantaneo = () => Promise.resolve();

describe("sondearEstadoTransaccion", () => {
  it("detecta el ÉXITO de la transacción que preparó", async () => {
    const leer = vi.fn().mockResolvedValue(transaccion("EXITO"));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir: dormirInstantaneo,
    });

    expect(resultado.estado).toBe("exito");
    expect(leer).toHaveBeenCalledTimes(1);
    expect(leer).toHaveBeenCalledWith(TRANSACCION_ID);
  });

  it("informa el RECHAZO definitivo en lugar de esperar", async () => {
    const leer = vi
      .fn()
      .mockResolvedValue(transaccion("FALLIDO", "Fondos insuficientes."));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir: dormirInstantaneo,
    });

    expect(resultado).toEqual({
      estado: "rechazado",
      mensaje: "Fondos insuficientes.",
    });
    expect(leer).toHaveBeenCalledTimes(1);
  });

  it("ACOTA la verificación y agota el intento", async () => {
    const leer = vi.fn().mockResolvedValue(transaccion("PENDIENTE"));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir: dormirInstantaneo,
    });

    expect(resultado.estado).toBe("timeout");
    expect(leer).toHaveBeenCalledTimes(MAX_SONDEOS);
  });

  it("sigue leyendo cuando UNA lectura falla: no es un pago fallido", async () => {
    const leer = vi
      .fn()
      .mockRejectedValueOnce(new Error("Network Error"))
      .mockResolvedValue(transaccion("EXITO"));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir: dormirInstantaneo,
    });

    expect(resultado.estado).toBe("exito");
    expect(leer).toHaveBeenCalledTimes(2);
  });

  it("se cancela cuando el checkout se cierra", async () => {
    const leer = vi.fn().mockResolvedValue(transaccion("PENDIENTE"));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir: dormirInstantaneo,
      cancelado: () => true,
    });

    expect(resultado.estado).toBe("cancelado");
    expect(leer).not.toHaveBeenCalled();
  });

  it("respeta el intervalo y el límite que se le pasan", async () => {
    const dormir = vi.fn().mockResolvedValue(undefined);
    const leer = vi.fn().mockResolvedValue(transaccion("PENDIENTE"));

    const resultado = await sondearEstadoTransaccion(TRANSACCION_ID, leer, {
      dormir,
      intervaloMs: 500,
      maxIntentos: 3,
    });

    expect(resultado.estado).toBe("timeout");
    expect(leer).toHaveBeenCalledTimes(3);
    // One wait less than the number of reads: the last read does not wait.
    expect(dormir).toHaveBeenCalledTimes(2);
    expect(dormir).toHaveBeenCalledWith(500);
  });

  it("expone el límite por defecto de la verificación", () => {
    expect(INTERVALO_SONDEO_MS).toBeGreaterThan(0);
    expect(MAX_SONDEOS).toBeGreaterThan(0);
  });
});

describe("esEstadoExito", () => {
  it("sólo EXITO prueba el pago", () => {
    expect(esEstadoExito("EXITO")).toBe(true);
    expect(esEstadoExito("PENDIENTE")).toBe(false);
    expect(esEstadoExito("FALLIDO")).toBe(false);
    expect(esEstadoExito("CANCELADO")).toBe(false);
    expect(esEstadoExito(null)).toBe(false);
    expect(esEstadoExito(undefined)).toBe(false);
  });
});
