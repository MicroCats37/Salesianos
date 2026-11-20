import { z } from "zod";

/**
 * The Zod mirror of `EdicionActualOut` (the `eventos` module).
 *
 * Owner: `Aplicacion/backend/modules/eventos/presentation/schemas/edicion_schemas.py`.
 * Route: `RT-ED-01` — `GET /api/ediciones/actual`, registered in
 * `Aplicacion/backend/config/api.py` (`EdicionController`).
 * Freeze: `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0`.
 *
 * The mirror is 1:1 with the THREE BLOCKS of `contract/SCHEMA_DRY_INTENTION.md`:
 * identity, general and specific. `modulos` is the addition of the "current
 * edition" case of use (`RN-E02`).
 *
 * There is no `z.any()` and no generic envelope: every field of the wrapper is
 * declared with its real type (`contract/api-wrapper-presenter-contract.md` §7).
 * The dates are ISO-8601 (`YYYY-MM-DD`) and the timestamps are ISO-8601
 * datetimes; the backend owns both and the frontend never re-formats them.
 */

/** IDENTITY block: identifiers and timestamps. */
export const EdicionIdentidadSchema = z.object({
  id: z.string().uuid(),
  created_at: z.string().datetime({ offset: true }),
  updated_at: z.string().datetime({ offset: true }),
});

/** GENERAL block: the event family the edition belongs to. */
export const EdicionGeneralSchema = z.object({
  evento_id: z.string().uuid(),
  evento_nombre: z.string(),
  evento_slug: z.string(),
});

/** SPECIFIC block: the data of the edition itself. */
export const EdicionEspecificaSchema = z.object({
  nombre: z.string(),
  slug: z.string(),
  anio: z.number().int(),
  estado: z.string(),
  modulos_habilitados: z.array(z.string()),
  fecha_inicio: z.iso.date().nullable(),
  fecha_fin: z.iso.date().nullable(),
});

/** The enablement state of one logical module of the edition (`RN-E02`). */
export const ModuloHabilitadoSchema = z.object({
  clave: z.string(),
  nombre: z.string(),
  habilitado: z.boolean(),
});

/**
 * The complete wrapper of the current edition (`EdicionActualOut`).
 *
 * It REPLACES the `edicionActualFixture` of UI-01: the provisional mirror of
 * the frozen presenter that lived in `features/public/fixtures/` is gone and
 * this is the only shape the public routes read.
 */
export const EdicionActualSchema = z.object({
  ...EdicionIdentidadSchema.shape,
  ...EdicionGeneralSchema.shape,
  ...EdicionEspecificaSchema.shape,
  modulos: z.array(ModuloHabilitadoSchema),
});

export type EdicionActual = z.infer<typeof EdicionActualSchema>;
export type ModuloHabilitado = z.infer<typeof ModuloHabilitadoSchema>;
