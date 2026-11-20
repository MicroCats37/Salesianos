import { z } from "zod";
import { envelopeAdmin } from "@/features/admin/operaciones/schemas/operaciones.schema";

/**
 * The Zod mirrors of the TRANSVERSAL summary.
 *
 * They are the 1:1 mirror of the backend `ResumenOperativoOut`
 * (`modules/administracion/presentation/schemas/admin_resumen_schemas.py`).
 *
 * A figure, an issue and a drilldown are FACTS of the backend: the browser
 * prints them and never re-derives them. A shape the mirror rejects is a LOUD
 * failure, not a screen with invented numbers.
 */

/** One figure of the summary. */
export const resumenMetricaSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  descripcion: z.string(),
  valor: z.number().int().nonnegative(),
});

/** The authorized action that resolves an issue. */
export const resumenAccionSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  href: z.string().min(1),
});

/** One visible problem of the edition. */
export const resumenIncidenciaSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  descripcion: z.string(),
  cantidad: z.number().int().nonnegative(),
  accion: resumenAccionSchema,
});

/** The summary of ONE edition. */
export const resumenOperativoSchema = z.object({
  edicion_id: z.string().min(1),
  edicion_nombre: z.string(),
  edicion_estado: z.string(),
  metricas: z.array(resumenMetricaSchema),
  incidencias: z.array(resumenIncidenciaSchema),
});

/** The success envelope of the summary. */
export const resumenOperativoEnvelope = envelopeAdmin(resumenOperativoSchema);
