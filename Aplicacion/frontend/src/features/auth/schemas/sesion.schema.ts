import { z } from "zod";

/**
 * The Zod mirror of `SesionUsuarioOut` (the `usuarios` module).
 *
 * Owner: `Aplicacion/backend/modules/usuarios/presentation/schemas/auth_schemas.py`.
 * Route: `GET /api/auth/me` — REGISTERED in `Aplicacion/backend/config/api.py`
 * (`AuthController`).
 *
 * Freeze: `FREEZE-ID-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0`.
 *
 * The wrapper is the composition of the THREE BLOCKS of
 * `contract/SCHEMA_DRY_INTENTION.md`:
 *
 * - `SesionIdentidadOut` — IDENTITY block.
 * - `SesionCuentaOut` — GENERAL block.
 * - `SesionRolOut` — SPECIFIC block: the facts of role, published by the
 *   BACKEND. The frontend draws them and never decides them.
 *
 * There is no `z.any()` and no generic envelope.
 */

/** IDENTITY block: the identifiers of the account and of its person. */
export const SesionIdentidadSchema = z.object({
  id: z.string(),
  persona_id: z.string().nullable(),
});

/** GENERAL block: the data of the account and of its person. */
export const SesionCuentaSchema = z.object({
  username: z.string(),
  email: z.string().nullable(),
  nombres: z.string().nullable(),
  apellidos: z.string().nullable(),
});

/**
 * SPECIFIC block: the facts of role.
 *
 * They are the authority of the server: the backend evaluates them again on
 * every request, so the client never caches a decision of its own.
 */
export const SesionRolSchema = z.object({
  rol: z.string(),
  grupos: z.array(z.string()),
  es_admin: z.boolean(),
  is_staff: z.boolean(),
  is_superuser: z.boolean(),
  nivel: z.string(),
  capacidades: z.array(z.string()),
});

/** The complete wrapper of the session (`SesionUsuarioOut`). */
export const SesionUsuarioSchema = z.object({
  ...SesionIdentidadSchema.shape,
  ...SesionCuentaSchema.shape,
  ...SesionRolSchema.shape,
});

export type SesionUsuario = z.infer<typeof SesionUsuarioSchema>;
