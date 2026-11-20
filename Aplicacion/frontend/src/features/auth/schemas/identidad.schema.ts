import { z } from "zod";

/**
 * The Zod mirrors of the identity wrappers (the `usuarios` module).
 *
 * Owner: `Aplicacion/backend/modules/usuarios/presentation/schemas/persona_schemas.py`.
 * Routes (all REGISTERED in `Aplicacion/backend/config/api.py`):
 *
 * - `RT-ID-01` — `GET /api/personas/busqueda/{documento}` → `DocumentoConsultaOut`.
 * - `RT-ID-02` — `POST /api/personas/resolver` → `PersonaResueltaOut`.
 * - `RT-ID-03` — `POST /api/personas/confirmar` → `PersonaOut`.
 *
 * Freeze: `FREEZE-ID-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0`.
 *
 * The mirrors are 1:1 with the THREE BLOCKS of
 * `contract/SCHEMA_DRY_INTENTION.md` and there is no `z.any()`: every field is
 * declared with its real type
 * (`contract/api-wrapper-presenter-contract.md` §7).
 */

/** GENERAL block: the civil identity of a person. */
export const PersonaDatosSchema = z.object({
  tipo_documento: z.string(),
  numero_documento: z.string(),
  nombres: z.string(),
  apellidos: z.string().nullable(),
});

/** IDENTITY block: identifiers, timestamps and the provenance of the data. */
export const PersonaIdentidadSchema = z.object({
  id: z.string().uuid(),
  origen_datos: z.string(),
  datos_obtenidos_en: z.string().datetime({ offset: true }).nullable(),
  creado_en: z.string().datetime({ offset: true }),
  actualizado_en: z.string().datetime({ offset: true }),
});

/**
 * `DocumentoConsultaOut` — the answer of the EXTERNAL source for a document.
 *
 * The source publishes the civil identity and NOTHING else: no internal
 * identifier travels in this answer.
 */
export const DocumentoConsultaSchema = z.object({
  tipo_documento: z.string(),
  numero_documento: z.string(),
  nombre_completo: z.string(),
});

/**
 * `PersonaResueltaOut` — the result of resolving a document.
 *
 * `persona_id` is `null` when the origin is `EXTERNO`: the identity exists in
 * the source but it is NOT persisted yet (`FR-03` §3.1).
 */
export const PersonaResueltaSchema = PersonaDatosSchema.extend({
  origen: z.string(),
  persona_id: z.string().uuid().nullable(),
  persistida: z.boolean(),
});

/** `PersonaOut` — a persisted person. */
export const PersonaSchema = PersonaDatosSchema.extend(
  PersonaIdentidadSchema.shape,
).extend({
  genero: z.string().nullable(),
});

/** `PersonaResolverIn` — the input of the resolver (`RT-ID-02`). */
export const PersonaResolverInSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
});

/** `PersonaConfirmarIn` — the input of the confirmation (`RT-ID-03`). */
export const PersonaConfirmarInSchema = z.object({
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  nombres: z.string().min(1).max(255),
  apellidos: z.string().max(255).nullable(),
  genero: z.string().max(1).nullable(),
});

export type DocumentoConsulta = z.infer<typeof DocumentoConsultaSchema>;
export type PersonaResuelta = z.infer<typeof PersonaResueltaSchema>;
export type Persona = z.infer<typeof PersonaSchema>;
export type PersonaResolverIn = z.infer<typeof PersonaResolverInSchema>;
export type PersonaConfirmarIn = z.infer<typeof PersonaConfirmarInSchema>;
