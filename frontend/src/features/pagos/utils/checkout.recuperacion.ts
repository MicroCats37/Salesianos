/**
 * Recovery of a payment whose provider relay was UNCERTAIN.
 *
 * The browser relay cannot be the only confirmation channel: when the popup
 * closes without a conclusive answer, the browser reads the state of the
 * transaction it prepared. The recovery is BOUNDED — it never turns into an
 * open-ended loop — and it only polls the transaction THIS checkout prepared.
 *
 * The module is dependency-injected on purpose: the reader and the wait are
 * parameters, so the behaviour can be verified deterministically without a
 * browser, a clock or a network.
 */

import type {
  TransaccionEstado,
  TransaccionEstadoResponse,
} from "../schemas/pago.schema";

/** Interval between two reads of the state of the attempt. */
export const INTERVALO_SONDEO_MS = 2000;

/** Maximum number of reads of a single recovery (30 seconds by default). */
export const MAX_SONDEOS = 15;

/**
 * Result of a bounded recovery.
 *
 * - `exito` — the attempt recorded a SUCCESS: the purchase state can be
 *   refreshed.
 * - `rechazado` — the attempt recorded a definitive failure: there is nothing
 *   to wait for.
 * - `timeout` — the bound was reached without a conclusive answer.
 * - `cancelado` — the recovery was cancelled (the checkout was closed).
 */
export type ResultadoRecuperacion =
  | { estado: "exito"; transaccion: TransaccionEstadoResponse["data"] }
  | { estado: "rechazado"; mensaje: string | null }
  | { estado: "timeout" }
  | { estado: "cancelado" };

/** Tunable parameters of a recovery. */
export interface OpcionesSondeo {
  /** Interval between two reads — defaults to {@link INTERVALO_SONDEO_MS}. */
  intervaloMs?: number;
  /** Maximum number of reads — defaults to {@link MAX_SONDEOS}. */
  maxIntentos?: number;
  /** Waits between two reads — injectable for the tests. */
  dormir?: (ms: number) => Promise<void>;
  /** Cancels the recovery when it returns true. */
  cancelado?: () => boolean;
}

/** Default wait between two reads. */
const dormirPorDefecto = (ms: number) =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });

/**
 * True when the attempt recorded a SUCCESS.
 *
 * Only `EXITO` is a success: every other state (including an unknown one)
 * keeps the conservative reading — the payment is not proven yet.
 */
export function esEstadoExito(
  estado: TransaccionEstado | string | null | undefined,
): boolean {
  return estado === "EXITO";
}

/**
 * Polls the state of the prepared transaction until it is conclusive.
 *
 * A failed read is NOT a failed payment: the attempt may still be recorded,
 * so the loop continues until the bound is reached. The recovery stops as
 * soon as the caller cancels it.
 */
export async function sondearEstadoTransaccion(
  transactionId: string,
  leer: (transactionId: string) => Promise<TransaccionEstadoResponse>,
  opciones: OpcionesSondeo = {},
): Promise<ResultadoRecuperacion> {
  const intervaloMs = opciones.intervaloMs ?? INTERVALO_SONDEO_MS;
  const maxIntentos = opciones.maxIntentos ?? MAX_SONDEOS;
  const dormir = opciones.dormir ?? dormirPorDefecto;
  const cancelado = opciones.cancelado ?? (() => false);

  for (let intento = 0; intento < maxIntentos; intento++) {
    if (cancelado()) return { estado: "cancelado" };

    let respuesta: TransaccionEstadoResponse;
    try {
      respuesta = await leer(transactionId);
    } catch {
      // A failed read is not a failed payment.
      respuesta = { success: false, data: null };
    }

    const transaccion = respuesta.data;
    const estado = transaccion?.status ?? null;

    if (esEstadoExito(estado)) {
      return { estado: "exito", transaccion };
    }

    if (estado === "FALLIDO" || estado === "CANCELADO") {
      return {
        estado: "rechazado",
        mensaje: transaccion?.response_message ?? null,
      };
    }

    if (intento < maxIntentos - 1) {
      await dormir(intervaloMs);
      if (cancelado()) return { estado: "cancelado" };
    }
  }

  return { estado: "timeout" };
}
