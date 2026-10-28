import { z } from "zod";
import { ADMIN_NIVELES } from "../utils/admin.capacidades";
import { AdminErrorSchema } from "./admin.comun.schema";

/**
 * AdminMeResponseSchema — mirror 1:1 of the backend `MeOut`
 * (`modules/usuarios/presentation/controllers/me_controller.py`).
 *
 * Endpoint: GET /api/auth/me  (A0)
 *
 * `es_admin` is computed on the server with the project rule:
 *
 *     admin = is_staff OR is_superuser
 *
 * It is the very same rule the backend `RequireAdmin` permission applies, so
 * the frontend can anticipate a refusal without ever being the authority: the
 * session cookie is advisory, the backend re-evaluates the flag on every
 * request (`sdd/administracion-operativa-fest/admin-surface` §6).
 *
 * `is_staff`, `is_superuser`, `nivel` and `capacidades` are SELF-SCOPED: the
 * endpoint publishes the tier of the CALLER, which is the base of the
 * interface and not a disclosure. The vocabulary is the mirror of
 * `backend/core/capacidades.py`.
 *
 * The new fields are TOLERANT (`default`): against an older backend the
 * interface degrades to "no capabilities" — it fails closed instead of
 * breaking the whole session.
 */
export const AdminMeResponseSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().nullable(),
  nombres: z.string().nullable(),
  apellidos: z.string().nullable(),
  rol: z.string().nullable(),
  es_admin: z.boolean(),
  is_staff: z.boolean().default(false),
  is_superuser: z.boolean().default(false),
  nivel: z
    .enum([
      ADMIN_NIVELES.USUARIO,
      ADMIN_NIVELES.STAFF,
      ADMIN_NIVELES.SUPERUSUARIO,
    ])
    .default(ADMIN_NIVELES.USUARIO),
  capacidades: z.array(z.string()).default([]),
  persona_id: z.string().nullable(),
});

export type AdminMeResponse = z.infer<typeof AdminMeResponseSchema>;

/** Mirror 1:1 of the backend `core.responses.ApiResponse` envelope. */
export const AdminMeEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminMeResponseSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminMeEnvelope = z.infer<typeof AdminMeEnvelopeSchema>;
