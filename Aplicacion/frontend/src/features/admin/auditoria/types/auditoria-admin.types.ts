import type { EstadoSuperficie } from "@/features/admin/operaciones";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";

/**
 * The view models of the ACTA of the sensitive actions.
 *
 * They mirror the backend `AuditoriaListadoOut` / `AuditoriaItemOut`
 * (`modules/administracion/presentation/schemas/admin_auditoria_schemas.py`),
 * 1:1 and without a single generic field.
 *
 * ## What the acta NAMES
 *
 * - WHO: the actor, by its legible name (the photo taken at the moment of
 *   the action).
 * - WHEN: the instant it was registered.
 * - WHAT: the code of the action and the entity it touched.
 * - WHY: the reason the actor wrote.
 *
 * ## What the acta does NOT publish
 *
 * The raw context of the action. The backend sanitises it when it WRITES
 * and publishes a white list when it READS: no secrets, no tokens, no
 * provider payloads and no internal identifiers (`XCT-02`).
 */
export interface AuditoriaItemOut {
  id: string;
  /** The edition the action belongs to, when it is scoped to one. */
  edicion_id: string | null;
  /** The legible name of the actor. Never an internal identifier. */
  actor: string;
  /** The stable code of the action (`RETIRAR_PARTICIPANTE`, …). */
  accion: string;
  /** The type of the entity the action touched. */
  entidad: string;
  /** The identifier of the entity the action touched. */
  entidad_id: string;
  /** WHY the action was executed. It is always present. */
  motivo: string;
  /** WHEN the action was registered. */
  registrado_en: string;
}

/** A page of the acta. */
export type AuditoriaListadoOut = PaginatedResult<AuditoriaItemOut>;

/** The state of the administrative read of the acta. */
export type EstadoAuditoriaAdmin = EstadoSuperficie<AuditoriaListadoOut>;
