/**
 * Tramite domain token constants — single source of truth for badge/label styling.
 *
 * Usage in components:
 *   import { ESTADO_SOLICITUD, PRIORIDAD_SOLICITUD, TIPO_ARCHIVO } from "@/shared/constants/tramite.tokens";
 *   <span className={ESTADO_SOLICITUD[solicitud.estado].badgeClass}>
 *     {ESTADO_SOLICITUD[solicitud.estado].label}
 *   </span>
 *
 * DO NOT hardcode inline badge classes in components — use these tokens.
 * Badge colors are centralized in globals.css: .badge-red, .badge-amber, .badge-neutral
 */

// ── Estado Solicitud ───────────────────────────────────────────────────────────

/**
 * V2 Django contract: estado values from backend enum.
 * Backend: REGISTRADA | EN_GESTION | FINALIZADA | ANULADA
 *
 * Color mapping (tonal scheme):
 *   REGISTRADA  → AMARILLO (warning/pending)
 *   EN_GESTION   → ROJO (critical/in-progress)
 *   FINALIZADA   → NEUTRAL (normal/closed)
 *   ANULADA      → ROJO (critical)
 */
export type EstadoSolicitud =
  | "REGISTRADA"
  | "EN_GESTION"
  | "FINALIZADA"
  | "ANULADA";

export const ESTADO_SOLICITUD: Record<
  EstadoSolicitud,
  { label: string; badgeClass: string }
> = {
  REGISTRADA: {
    label: "Registrada",
    badgeClass: "badge-amber",
  },
  EN_GESTION: {
    label: "En Gestión",
    badgeClass: "badge-red",
  },
  FINALIZADA: {
    label: "Finalizada",
    badgeClass: "badge-neutral",
  },
  ANULADA: {
    label: "Anulada",
    badgeClass: "badge-red",
  },
};

// ── Prioridad Solicitud ───────────────────────────────────────────────────────

/**
 * V2 Django contract: prioridad values from backend enum.
 * Backend: BAJA | MEDIA | ALTA | URGENTE
 *
 * Color mapping (tonal scheme):
 *   BAJA   → NEUTRAL (normal/low)
 *   MEDIA  → AMARILLO (warning)
 *   ALTA   → ROJO (critical)
 *   URGENTE → ROJO (critical)
 */
export type PrioridadSolicitud = "BAJA" | "MEDIA" | "ALTA" | "URGENTE";

export const PRIORIDAD_SOLICITUD: Record<
  PrioridadSolicitud,
  { label: string; badgeClass: string }
> = {
  BAJA: {
    label: "Baja",
    badgeClass: "badge-neutral",
  },
  MEDIA: {
    label: "Media",
    badgeClass: "badge-amber",
  },
  ALTA: {
    label: "Alta",
    badgeClass: "badge-red",
  },
  URGENTE: {
    label: "Urgente",
    badgeClass: "badge-red",
  },
};

// ── Tipo Persona ───────────────────────────────────────────────────────────────

/**
 * Backend: NATURAL | JURIDICA | COLEGIADO
 *
 * Color mapping: these are informational categories, mapped to neutral.
 */
export type TipoPersona = "NATURAL" | "JURIDICA" | "COLEGIADO";

export const TIPO_PERSONA: Record<
  TipoPersona,
  { label: string; badgeClass: string }
> = {
  NATURAL: {
    label: "Persona Natural",
    badgeClass: "badge-neutral",
  },
  JURIDICA: {
    label: "Persona Jurídica",
    badgeClass: "badge-neutral",
  },
  COLEGIADO: {
    label: "Colegiado",
    badgeClass: "badge-neutral",
  },
};

// ── Tipo Archivo ──────────────────────────────────────────────────────────────

/**
 * Backend: PRINCIPAL | ANEXO
 *
 * Color mapping:
 *   PRINCIPAL → ROJO (primary/important)
 *   ANEXO     → NEUTRAL (secondary/supporting)
 */
export type TipoArchivo = "PRINCIPAL" | "ANEXO";

export const TIPO_ARCHIVO: Record<
  TipoArchivo,
  { label: string; badgeClass: string }
> = {
  PRINCIPAL: {
    label: "Principal",
    badgeClass: "badge-red",
  },
  ANEXO: {
    label: "Anexo",
    badgeClass: "badge-neutral",
  },
};

// ── Tipo Participacion ───────────────────────────────────────────────────────

/**
 * Backend: PRINCIPAL | ADJUNTA
 *
 * Color mapping:
 *   PRINCIPAL → ROJO (primary)
 *   ADJUNTA  → NEUTRAL (secondary)
 */
export type TipoParticipacion = "PRINCIPAL" | "ADJUNTA";

export const TIPO_PARTICIPACION: Record<
  TipoParticipacion,
  { label: string; badgeClass: string }
> = {
  PRINCIPAL: {
    label: "Principal",
    badgeClass: "badge-red",
  },
  ADJUNTA: {
    label: "Adjunta",
    badgeClass: "badge-neutral",
  },
};

// ── Estado Periodo ───────────────────────────────────────────────────────────

/**
 * Backend: PENDIENTE | EN_GESTION | CERRADO
 *
 * Color mapping:
 *   PENDIENTE  → AMARILLO (warning/pending)
 *   EN_GESTION → ROJO (critical/in-progress)
 *   CERRADO    → NEUTRAL (normal/closed)
 */
export type EstadoPeriodo = "PENDIENTE" | "EN_GESTION" | "CERRADO";

export const ESTADO_PERIODO: Record<
  EstadoPeriodo,
  { label: string; badgeClass: string }
> = {
  PENDIENTE: {
    label: "Pendiente",
    badgeClass: "badge-amber",
  },
  EN_GESTION: {
    label: "En Gestión",
    badgeClass: "badge-red",
  },
  CERRADO: {
    label: "Cerrado",
    badgeClass: "badge-neutral",
  },
};

// ── Estado Individual de Notificación ────────────────────────────────────────

/**
 * Backend: NO_VISTA | VISTA | ABIERTA | DESCARTADA
 * Representa el estado individual de la interacción del usuario con la notificación.
 *
 * Color mapping (tonal scheme):
 *   NO_VISTA    → ROJO (critical/new)
 *   VISTA       → AMARILLO (warning/seen but not acted)
 *   ABIERTA     → AMARILLO (warning/open)
 *   DESCARTADA  → NEUTRAL (normal/dismissed)
 */
export type EstadoNotificacionIndividual =
  | "NO_VISTA"
  | "VISTA"
  | "ABIERTA"
  | "DESCARTADA";

export const ESTADO_NOTIFICACION: Record<
  EstadoNotificacionIndividual,
  { label: string; badgeClass: string }
> = {
  NO_VISTA: {
    label: "No vista",
    badgeClass: "badge-red",
  },
  VISTA: {
    label: "Vista",
    badgeClass: "badge-amber",
  },
  ABIERTA: {
    label: "Abierta",
    badgeClass: "badge-amber",
  },
  DESCARTADA: {
    label: "Descartada",
    badgeClass: "badge-neutral",
  },
};
