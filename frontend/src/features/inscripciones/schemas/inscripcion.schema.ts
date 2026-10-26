import { z } from "zod";
import { ParticipanteSchema } from "./participante.schema";

export type { ParticipanteFormData } from "./participante.schema";
export {
  CE_REGEX,
  DNI_REGEX,
  GeneroEnum,
  PAS_REGEX,
  PHONE_REGEX,
  TipoDocumentoEnum,
} from "./participante.schema";

// ── Phase 2: Summary / Aggregate Schemas ────────────────────────────────────────
// These Zod schemas mirror the backend Pydantic schemas in inscripcion_schemas.py
// (Phase 2 output schemas). The frontend schemas are the authoritative contract for
// what the API returns — they must stay in sync when backend adds fields.

/**
 * Payment-order summary — mirrors backend `OrdenPagoResumenSchema`.
 * Contract: `OrdenPago.metadata` is NEVER exposed here.
 */
export const OrdenPagoResumenSchema = z.object({
  id: z.string(),
  numero: z.string(),
  estado: z.string(),
  pagada_en: z.string().nullable().optional(),
});

export type OrdenPagoResumen = z.infer<typeof OrdenPagoResumenSchema>;

/**
 * Commercial purchase summary — mirrors backend `CompraResumenSchema`.
 * Contract: `Compra.metadata` is NEVER exposed here.
 */
export const CompraResumenSchema = z.object({
  id: z.string(),
  tipo: z.string(), // INICIAL | AMPLIACION
  cantidad: z.number().int(),
  precio_unitario: z.number(),
  total: z.number(),
  estado: z.string(), // PENDIENTE | PAGADA | CANCELADA
  orden_pago: OrdenPagoResumenSchema.nullable().optional(),
});

export type CompraResumen = z.infer<typeof CompraResumenSchema>;

/**
 * Aggregate payment/commercial summary — mirrors backend `ResumenPagoSchema`.
 * Computed by the presenter from compras + ordenes.
 * Never mutates or infers `Inscripcion.estado` from payment state.
 */
export const ResumenPagoSchema = z.object({
  total_compras: z.number().int(),
  total_contratado: z.number().int(), // sum of quantities of non-cancelled purchases
  total_pagado: z.number(), // sum of monetary totals of PAGADA purchases
  total_pagado_cantidad: z.number().int(), // sum of quantities of PAGADA purchases
  compras_pendientes: z.number().int(),
  compras_pagadas: z.number().int(),
  compras_canceladas: z.number().int(),
  disponible_pagado: z.number().int(), // free paid slots = total_pagado_cantidad - active assignments (asignados_pagados)
  estado_mensaje: z.string(), // UI message: "Sin actividades de pago" | "Pago pendiente" | "Pago parcial" | "Pago confirmado"
  compras: z.array(CompraResumenSchema),
});

export type ResumenPago = z.infer<typeof ResumenPagoSchema>;

/**
 * Aggregate team-roster summary — mirrors backend `ResumenEquiposSchema`.
 * Computed by the presenter from equipo roster states.
 */
export const ResumenEquiposSchema = z.object({
  total: z.number().int(),
  completos: z.number().int(), // equipos with estado_roster == COMPLETO
  incompletos: z.number().int(), // equipos with estado_roster == INCOMPLETO
});

export type ResumenEquipos = z.infer<typeof ResumenEquiposSchema>;

// ── Equipo Schema ─────────────────────────────────────────────────────────────

export const EquipoSchema = z.object({
  disciplina_id: z.string().min(1, "Selecciona una disciplina"),
  categoria_id: z.string().nullable().optional(),
  nombre: z.string().min(1, "Nombre del equipo requerido").max(120),
  // Draft inscriptions may be created without participants. Roster min/max is
  // validated later by the backend when the inscription is reviewed/confirmed.
  participantes: z.array(ParticipanteSchema),
});

export type EquipoFormData = z.infer<typeof EquipoSchema>;

// ── Main Inscripcion Schema ────────────────────────────────────────────────────

export const InscripcionFormSchema = z.object({
  // Catalog IDs (evento is NOT a client input — resolved server-side)
  paquete_id: z.string().min(1, "Selecciona un paquete"),
  promocion_id: z.string().min(1, "Selecciona tu promoción"),
  fusion_promocion_id: z.string().nullable().optional(),

  // Equipos — array (paquete puede incluir varias disciplinas)
  equipos: z.array(EquipoSchema).min(1, "Agrega al menos un equipo"),

  // Cantidad comercial — set by SmartPaqueteCardsField when a card is selected.
  // Optional: server falls back to paquete.cantidad_minima_compra when absent.
  // Server-authoritative: revalidated against paquete.minimo_compra_inicial.
  cantidad: z.number().int().min(1).optional(),

  // Propagación de la cotización al backend.
  // SmartPaqueteCardsField hace setValue de ambos campos en handleSelect
  // cuando el usuario confirma el card — esto garantiza que el backend
  // reciba el MISMO precio_unitario que el usuario vio en pantalla.
  // precio_unitario_cotizado y cotizacion_version son opcionales: si no
  // se enviaron, el backend usa el precio vigente del catálogo.
  precio_unitario_cotizado: z.number().positive().optional(),
  cotizacion_version: z.number().int().positive().optional(),
});

export type InscripcionFormData = z.infer<typeof InscripcionFormSchema>;

// ── Backend Payload Mapping ─────────────────────────────────────────────────────

/**
 * Maps frontend camelCase to the backend expected snake_case payload.
 * Backend CrearInscripcionIn requires: evento_id, paquete_id,
 * promocion_id, fusion_promocion_id, estado (default BORRADOR).
 *
 * NOTE: responsable_id is derived server-side from the authenticated user.
 * Client must NOT send it.
 *
 * NOTE: Consent fields are NOT in the form schema. They live in LOCAL
 * InscripcionWizard state and are validated manually in `onSubmit`. The wizard
 * shows a blocking toast if any consent is missing. Aceptaciones themselves
 * are recorded per-person via POST /{inscripcion_id}/personas — never sent
 * in the InscripcionCompletaPayload.
 *
 * NOTE: atomic creation payload (POST /inscripciones/completa/) is built
 * directly inside `useCreateInscripcionCompleta` from form state — there is
 * NO intermediate mapping function. The wizard component assembles the
 * payload from `paquetes?.find(id === watched)` and form data.
 */
export interface InscripcionBackendPayload {
  evento_id: string;
  paquete_id: string;
  promocion_id: string;
  fusion_promocion_id?: string | null;
  estado?: string;
}

export function toBackendPayload(
  data: InscripcionFormData,
  evento_id: string,
): InscripcionBackendPayload {
  return {
    evento_id,
    paquete_id: data.paquete_id,
    promocion_id: data.promocion_id,
    fusion_promocion_id: data.fusion_promocion_id ?? null,
    estado: "BORRADOR",
  };
}
