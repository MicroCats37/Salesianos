import { z } from "zod";

// ── Cotizacion Schemas ───────────────────────────────────────────────────────────

/**
 * Request payload for POST /api/cotizaciones/
 */
export const CotizacionRequestSchema = z.object({
  paquete_id: z.string().min(1, "paquete_id requerido"),
  cantidad: z.number().int().min(1, "cantidad debe ser al menos 1"),
});

export type CotizacionRequest = z.infer<typeof CotizacionRequestSchema>;

/**
 * Response from the quotation endpoint — matches CotizacionResponse backend schema.
 */
export const CotizacionResponseSchema = z.object({
  paquete_id: z.string(),
  paquete_nombre: z.string(),
  modo_disciplinas: z.enum(["FIJO", "ELEGIBLE"]),
  minimo_cantidad: z.number().int().min(1),
  cantidad_cotizada: z.number().int().min(1),
  precio_unitario: z.number(),
  precio_regular: z.number(),
  precio_preventa: z.number().nullable(),
  total: z.number(),
  validez_hasta: z.string().datetime(),
  version: z.number().int(),
  estado: z.enum(["ACTIVA", "EXPIRADA"]),
});

export type CotizacionResponse = z.infer<typeof CotizacionResponseSchema>;
