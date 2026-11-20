import { z } from "zod";
import {
  envelopeAdmin,
  envelopeAdminPaginado,
} from "@/features/admin/operaciones/schemas/operaciones.schema";
import {
  eventoDeHistorialAdminSchema,
  participacionAdminSchema,
} from "@/features/admin/participantes/schemas/participante-admin.schema";

/**
 * The Zod mirror of the administrative search of PEOPLE.
 *
 * It is the 1:1 mirror of the backend `AdminPersonaListItemOut` /
 * `AdminPersonaDetalleOut`.
 *
 * ## What it is NOT
 *
 * `AdminPersonaController` is NOT registered in
 * `Aplicacion/backend/config/api.py`, so `RT-ID-07` and `RT-ID-08` do NOT
 * exist and no answer of the backend is ever parsed with this mirror. It is
 * the SEAM of the contract (`A0-XCT02-01`).
 *
 * ## ONE owner for ONE shape
 *
 * The wire of a person IS the wire of a participant: the mirrors of the
 * participations are REUSED here instead of being declared twice.
 */

/** A person of the administrative search. */
export const adminPersonaListItemSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
  documento: z.string(),
  participaciones: z.array(participacionAdminSchema),
  historial: z.array(eventoDeHistorialAdminSchema),
});

/** The detail of a person (`RT-ID-08`). */
export const adminPersonaDetalleSchema = adminPersonaListItemSchema.extend({
  telefono: z.string(),
  whatsapp: z.string(),
  email: z.string(),
});

/** The success envelope of the administrative search (`RT-ID-07`). */
export const listaPersonasAdminEnvelope = envelopeAdminPaginado(
  adminPersonaListItemSchema,
);

/** The success envelope of the detail of a person (`RT-ID-08`). */
export const adminPersonaDetalleEnvelope = envelopeAdmin(
  adminPersonaDetalleSchema,
);

/** The wire of a person of the administrative search. */
export type AdminPersonaListItemWire = z.infer<
  typeof adminPersonaListItemSchema
>;

/** The wire of the detail of a person. */
export type AdminPersonaDetalleWire = z.infer<typeof adminPersonaDetalleSchema>;
