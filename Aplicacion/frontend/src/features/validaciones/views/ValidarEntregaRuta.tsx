"use client";

import { useCallback, useMemo, useState } from "react";
import { handleApiError } from "@/errors";
import { useSesionActual } from "@/features/auth/hooks";
import {
  useConfirmarTicket,
  usePreviewTicket,
} from "../hooks/useValidacion";
import type {
  EstadoVistaValidaciones,
  ResultadoValidacion,
  VistaPreviaValidacion,
} from "../types/validacion.types";
import {
  adaptarPreview,
  adaptarResultado,
} from "../utils/validaciones.preview.utils";
import { ValidarEntregaView } from "./ValidarEntregaView";

/**
 * The point of control of the DELIVERY.
 *
 * It is the LABEL of this screen, not a business fact: the frozen preview
 * does not publish a point of control.
 */
const PUNTO_ENTREGA = "Mostrador de recogidas";

/**
 * The container of `ADM-20`, the DELIVERY of the store.
 *
 * The page (`src/app/(administracion)/administracion/marketplace/entregas/page.tsx`)
 * is ROUTING-ONLY: this container owns the check and the confirmation, and the
 * VIEW owns the drawing.
 *
 * **IT IS NOT THE ENTRY.** The delivery consumes a PAID ORDER and the entry
 * consumes a RIGHT OF ENTRY. They share the client, the schemas and the
 * components, and each one asks the backend about its OWN subject: the
 * backend resolves the delivery against `marketplace` and the entry against
 * `salesianos_fest` (`FR-05` §5).
 *
 * **THE MANUAL CODE IS THE FALLBACK.** The operator may scan the code or
 * TYPE it: the console of `UI-05` has both, and the typed one is the path
 * that always works.
 */
export function ValidarEntregaRuta() {
  const sesion = useSesionActual();
  const comprobar = usePreviewTicket();
  const confirmar = useConfirmarTicket();

  const [vistaPrevia, setVistaPrevia] = useState<VistaPreviaValidacion | null>(
    null,
  );
  const [resultado, setResultado] = useState<ResultadoValidacion | null>(null);
  const [codigo, setCodigo] = useState<string | null>(null);
  const [clave, setClave] = useState<string | null>(null);

  const contexto = useMemo(
    () => ({ punto: PUNTO_ENTREGA, operador: nombreDelOperador(sesion.data) }),
    [sesion.data],
  );

  const onComprobar = useCallback(
    (codigoComprobado: string) => {
      setResultado(null);
      setVistaPrevia(null);
      setCodigo(codigoComprobado);
      comprobar.mutate(codigoComprobado, {
        onSuccess: (datos) => {
          setVistaPrevia(adaptarPreview(datos, contexto));
          setClave(claveDeIdempotencia(codigoComprobado));
        },
      });
    },
    [comprobar, contexto],
  );

  const onConfirmar = useCallback(() => {
    if (!codigo || !clave) return;
    confirmar.mutate(
      { codigo, idempotency_key: clave },
      {
        onSuccess: (datos) => setResultado(adaptarResultado(datos, contexto)),
      },
    );
  }, [confirmar, codigo, clave, contexto]);

  const error = comprobar.error ? handleApiError(comprobar.error) : null;

  const estado: EstadoVistaValidaciones =
    comprobar.isPending || confirmar.isPending
      ? "cargando"
      : error
        ? error.status === 403
          ? "sin-permiso"
          : "error"
        : "listo";

  return (
    <ValidarEntregaView
      estado={estado}
      vistaPrevia={vistaPrevia ?? undefined}
      resultado={resultado ?? undefined}
      onComprobar={onComprobar}
      onConfirmar={vistaPrevia?.puede_validar ? onConfirmar : undefined}
      ocupado={comprobar.isPending || confirmar.isPending}
    />
  );
}

/**
 * The idempotency key of ONE intention.
 *
 * It identifies the confirmation of ONE credential: the retry of the same
 * intention reuses it and the backend returns the same record
 * (`FR-04` §2.2).
 */
function claveDeIdempotencia(codigo: string): string {
  const sufijo =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `validacion:${codigo}:${sufijo}`;
}

/** The name of the operator, as the session publishes it. */
function nombreDelOperador(sesion: unknown): string {
  const cuenta = (
    sesion as
      | {
          cuenta?: {
            nombres?: string | null;
            apellidos?: string | null;
            username?: string;
          };
        }
      | undefined
  )?.cuenta;
  if (!cuenta) return "";
  const nombre = [cuenta.nombres, cuenta.apellidos].filter(Boolean).join(" ");
  return nombre || cuenta.username || "";
}
