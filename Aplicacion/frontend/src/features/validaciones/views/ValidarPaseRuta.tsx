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
import { ValidarPaseView } from "./ValidarPaseView";

/**
 * The point of control of the ENTRY.
 *
 * It is the LABEL of this screen, not a business fact: the frozen preview
 * does not publish a point of control.
 */
const PUNTO_ENTRADA = "Control de acceso";

/**
 * The container of `ADM-16`, the ENTRY control of the party.
 *
 * The page (`src/app/(administracion)/administracion/pases/validar/page.tsx`)
 * is ROUTING-ONLY: this container owns the check and the confirmation, and the
 * VIEW owns the drawing.
 *
 * **THE TWO OPERATIONS ARE NEVER MERGED.** This container is the ENTRY: it
 * reads a credential of a right of entry. The delivery has its own container
 * (`ValidarEntregaRuta`) and its own decision. They share the CLIENT, the
 * SCHEMAS and the components, and nothing else (`RB-07`).
 *
 * **THE MANUAL CODE IS THE FALLBACK.** The operator may scan the code or
 * TYPE it: the console of `UI-05` has both, and the typed one is the path
 * that always works.
 *
 * **THE SERVER DECIDES.** The container never decides that a credential can
 * be redeemed: it offers the confirmation only when the server said so
 * (`puede_canjear`).
 */
export function ValidarPaseRuta() {
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
    () => ({ punto: PUNTO_ENTRADA, operador: nombreDelOperador(sesion.data) }),
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
          // Una comprobación abre UNA intención: la clave de idempotencia se
          // crea aquí y se reutiliza en los reintentos de la misma intención.
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
    <ValidarPaseView
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
  const cuenta = (sesion as { cuenta?: { nombres?: string | null; apellidos?: string | null; username?: string } } | undefined)?.cuenta;
  if (!cuenta) return "";
  const nombre = [cuenta.nombres, cuenta.apellidos].filter(Boolean).join(" ");
  return nombre || cuenta.username || "";
}
