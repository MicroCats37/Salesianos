/**
 * traceabilityLabels — centralized Spanish humanizers for traceability enums.
 *
 * Guarantees (audit F14):
 * - Known enums map to neutral Spanish labels.
 * - Unknown values NEVER leak snake_case to the UI: they fall back to a
 *   humanized version of the raw value (lowercase, underscores → spaces).
 * - null/empty → "Sin dato".
 *
 * Fallback policy (documented): for unknown values we prefer a humanized raw
 * value (e.g. "ESTADO_EXTRA" → "Estado extra") over a fixed "Otro", because it
 * keeps the payload auditable while remaining readable. The fixed "Otro" is
 * only used for the domain-level OTRO response type, never as a catch-all.
 */

import {
  ESTADO_PERIODO,
  ESTADO_SOLICITUD,
  TIPO_PARTICIPACION,
} from "../../../../shared/constants/tramite.tokens";
import { TIPO_RESPUESTA_LABELS } from "../../schemas/finalizar-solicitud.schema";

const FALLBACK_EMPTY = "Sin dato";

function pick<T>(
  source: Readonly<Record<string, T>>,
  key: string | null | undefined,
): T | undefined {
  if (key == null) return undefined;
  return source[key];
}

/** Humanize any raw enum value; never returns snake_case. */
export function humanizeEnum(raw: string | null | undefined): string {
  if (raw == null || raw.trim() === "") return FALLBACK_EMPTY;
  const cleaned = raw
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

/** Global Solicitud state (ESTADO_SOLICITUD). */
export function solicitudEstadoLabel(
  estado: string | null | undefined,
): string {
  return pick(ESTADO_SOLICITUD, estado)?.label ?? humanizeEnum(estado);
}

/** Period/cycle operational state (ESTADO_PERIODO). */
export function periodoEstadoLabel(estado: string | null | undefined): string {
  return pick(ESTADO_PERIODO, estado)?.label ?? humanizeEnum(estado);
}

/** Participation type (TIPO_PARTICIPACION). */
export function participacionLabel(tipo: string | null | undefined): string {
  return pick(TIPO_PARTICIPACION, tipo)?.label ?? humanizeEnum(tipo);
}

/** Formal response type (TIPO_RESPUESTA_LABELS). */
export function respuestaLabel(tipo: string | null | undefined): string {
  return pick(TIPO_RESPUESTA_LABELS, tipo) ?? humanizeEnum(tipo);
}

/** Response lifecycle state (EstadoRespuesta). */
export function respuestaEstadoLabel(
  estado: string | null | undefined,
): string {
  return pick(RESPUESTA_ESTADO_LABELS, estado) ?? humanizeEnum(estado);
}

/** Event type (TimelineEventOut.tipo). */
export function eventoTipoLabel(tipo: string | null | undefined): string {
  return pick(EVENTO_TIPO_LABELS, tipo) ?? humanizeEnum(tipo);
}

/** Period closure type (TipoCierre). */
export function tipoCierreLabel(tipo: string | null | undefined): string {
  return pick(TIPO_CIERRE_LABELS, tipo) ?? humanizeEnum(tipo);
}

const EVENTO_TIPO_LABELS: Record<string, string> = {
  // Canonical backend event types (solicitud_trazabilidad_presenter).
  ESTADO_SOLICITUD: "Estado de la solicitud",
  AREA_INCORPORADA: "Área incorporada",
  PERIODO_INICIADO: "Ciclo iniciado",
  PERIODO_CERRADO: "Ciclo cerrado",
  PARTICIPANTE_AGREGADO: "Participante agregado",
  PARTICIPANTE_RETIRO: "Participante retirado",
  RESPUESTA_EMITIDA: "Respuesta emitida",
  // Alias spellings kept for forward-compat with future payloads.
  ESTADO_SOLICITUD_CAMBIADO: "Estado de la solicitud",
  ESTADO_PERIODO_CAMBIADO: "Cambio de estado del ciclo",
  PERIODO_ESTADO_CAMBIADO: "Cambio de estado del ciclo",
  PARTICIPANTE_RETIRADO: "Participante retirado",
  RESPUESTA_REGISTRADA: "Respuesta registrada",
};

const TIPO_CIERRE_LABELS: Record<string, string> = {
  FINALIZADO: "Finalizado",
  DERIVADO: "Derivado",
  RETIRADO: "Retirado",
  RECHAZADO: "Rechazado",
  ANULADO: "Anulado",
  ASIGNACION_ERRONEA: "Asignación errónea",
  CAMBIO_PARTICIPACION: "Cambio de participación",
};

const RESPUESTA_ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  EMITIDA: "Emitida",
  ANULADA: "Anulada",
  RECTIFICADA: "Rectificada",
};
