import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";

/**
 * AdminMeResponseSchema — mirror 1:1 of the backend `MeOut`
 * (`modules/usuarios/presentation/controllers/me_controller.py`).
 *
 * Endpoint: GET /api/auth/me  (A0)
 *
 * `es_admin` is the ONLY authorization flag the client consumes and it is
 * computed on the server with the project rule:
 *
 *     admin = is_staff OR is_superuser
 *
 * It is the very same rule the backend `RequireAdmin` permission applies, so
 * the frontend can anticipate a refusal without ever being the authority: the
 * session cookie is advisory, the backend re-evaluates the flag on every
 * request (`sdd/administracion-operativa-fest/admin-surface` §6).
 *
 * `is_superuser` is NEVER exposed: the break-glass tier is neither visible
 * nor assignable from the administration UI.
 */
export const AdminMeResponseSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().nullable(),
  nombres: z.string().nullable(),
  apellidos: z.string().nullable(),
  rol: z.string().nullable(),
  es_admin: z.boolean(),
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
