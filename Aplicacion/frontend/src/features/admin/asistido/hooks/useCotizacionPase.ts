"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { mensajeDeError } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { cotizarPaseCliente } from "../services/asistido.service";
import type { CotizacionPaseClienteOut } from "../types/asistido.types";

/**
 * The QUOTATION of a pass for the assisted purchase.
 *
 * ## Why the quotation lives in local state
 *
 * The quotation is EPHEMERAL: it belongs to ONE pass AND ONE quantity, the
 * ones that are on the screen right now. It is not a dataset of the server,
 * so it does not live in the cache of TanStack Query (which holds the reads
 * that the server owns) and the token of the price is NEVER cached.
 *
 * ## The sequence guard
 *
 * Two quotations can be in flight at once (the administrator changes the
 * quantity while a request is travelling). Without the guard the slowest
 * answer wins and the form shows a total that belongs to another quantity,
 * so only the NEWEST request may write the state.
 *
 * ## The debounce
 *
 * The quantity is a control that the administrator types: every keystroke
 * would be a request. The remote work is debounced so that only the last
 * value travels.
 */

/** How long the hook waits before it asks the server for a quotation. */
const ESPERA_COTIZACION_MS = 300;

export interface CotizacionPase {
  /** The last quotation that the server answered. */
  cotizacion: CotizacionPaseClienteOut | null;
  /** Whether a request is travelling. */
  estaCotizando: boolean;
  /** The public prose of the last failure, verbatim. */
  fallo: string | null;
  /** Ask the server for the quotation of a pass and a quantity. */
  cotizar: (paseId: string, cantidad: number) => void;
  /** Drop the current quotation: it belongs to a quantity that is gone. */
  invalidar: () => void;
}

export function useCotizacionPase(): CotizacionPase {
  const [cotizacion, setCotizacion] = useState<CotizacionPaseClienteOut | null>(
    null,
  );
  const [estaCotizando, setEstaCotizando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);

  /**
   * The sequence of the requests: only the newest one may write the state.
   */
  const secuencia = useRef(0);

  /** The pending debounce, if any. */
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Whether the hook is still mounted. */
  const vivo = useRef(true);

  useEffect(() => {
    return () => {
      vivo.current = false;
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  /**
   * Drop the current quotation.
   *
   * It is used when the quantity changes: the quotation belongs to the
   * previous combination and it must not be shown (nor written to the form)
   * until the new one arrives.
   */
  const invalidar = useCallback(() => {
    secuencia.current += 1;

    if (temporizador.current) {
      clearTimeout(temporizador.current);
      temporizador.current = null;
    }

    setCotizacion(null);
    setFallo(null);
    setEstaCotizando(false);
  }, []);

  /**
   * Ask the server for the quotation of a pass and a quantity.
   *
   * It depends on NOTHING that changes on every render: the request is
   * scheduled here and the sequence number decides which answer may write
   * the state.
   */
  const cotizar = useCallback((paseId: string, cantidad: number) => {
    const numero = ++secuencia.current;

    if (temporizador.current) clearTimeout(temporizador.current);

    setEstaCotizando(true);

    temporizador.current = setTimeout(() => {
      temporizador.current = null;

      cotizarPaseCliente({ pase_id: paseId, cantidad })
        .then((respuesta) => {
          // An answer that belongs to a quantity that is no longer the
          // current one must not write the state.
          if (!vivo.current || numero !== secuencia.current) return;

          setCotizacion(respuesta);
          setFallo(null);
          setEstaCotizando(false);
        })
        .catch((error: unknown) => {
          if (!vivo.current || numero !== secuencia.current) return;

          setCotizacion(null);
          setFallo(mensajeDeError(error));
          setEstaCotizando(false);
        });
    }, ESPERA_COTIZACION_MS);
  }, []);

  return {
    cotizacion,
    estaCotizando,
    fallo,
    cotizar,
    invalidar,
  };
}
