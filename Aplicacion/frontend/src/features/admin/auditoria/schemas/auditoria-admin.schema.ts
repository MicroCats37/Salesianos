import { z } from "zod";
import { envelopeAdminPaginado } from "@/features/admin/operaciones/schemas/operaciones.schema";

/**
 * The Zod mirror of the ACTA of the sensitive actions.
 *
 * It is the 1:1 mirror of the backend `AuditoriaItemOut` /
 * `AuditoriaListadoOut` (`modules/administracion/presentation/schemas/
 * admin_auditoria_schemas.py`).
 *
 * ## What it is NOT
 *
 * `AdminController` is NOT registered in `Aplicacion/backend/config/api.py`,
 * so `RT-ADM-02` does NOT exist and no answer of the backend is ever parsed
 * with this mirror. It is the SEAM of the contract: the day A0 registers
 * the controller, this mirror is the first thing to reconcile
 * (`A0-XCT02-01`).
 *
 * ## The rules of the mirror
 *
 * - No `z.any()` and no generic field: every field is declared.
 * - The codes are `string`, not enums: the backend owns the vocabulary and
 *   a new value must not break the whole read.
 * - The acta publishes a WHITE LIST: there is NO field of raw context.
 */

/**
 * One entry of the acta.
 *
 * It is STRICT: the acta publishes a WHITE LIST and a field that the server
 * does not publish is a contract violation, not a field to ignore. An entry
 * that carries a raw context (`contexto`) is REJECTED instead of being
 * silently stripped, because a stripped context would hide the very leak the
 * acta exists to prevent.
 */
export const auditoriaItemSchema = z
  .object({
    id: z.string().min(1),
    edicion_id: z.string().nullable(),
    actor: z.string(),
    accion: z.string().min(1),
    entidad: z.string(),
    entidad_id: z.string(),
    motivo: z.string(),
    registrado_en: z.string().min(1),
  })
  .strict();

/** A page of the acta. */
export const auditoriaListadoSchema = z.object({
  items: z.array(auditoriaItemSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  total_pages: z.number().int().nonnegative(),
});

/** The success envelope of the read of the acta (`RT-ADM-02`). */
export const auditoriaListadoEnvelope =
  envelopeAdminPaginado(auditoriaItemSchema);

/** The wire of one entry of the acta. */
export type AuditoriaItemWire = z.infer<typeof auditoriaItemSchema>;

/** The wire of a page of the acta. */
export type AuditoriaListadoWire = z.infer<typeof auditoriaListadoSchema>;
