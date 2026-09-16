import { z } from "zod";

// ── Step 3: Detalle de la Reclamación ────────────────────────────────────────

export const DetalleReclamacionSchema = z.object({
  tipo_reclamacion: z.enum(["RECLAMO", "QUEJA"], {
    message: "Selecciona el tipo de reclamación",
  }),
  area_oficina: z
    .string()
    .min(1, "El área u oficina es requerida")
    .max(200, "Máximo 200 caracteres"),
  descripcion_detalle: z
    .string()
    .min(10, "La descripción debe tener al menos 10 caracteres")
    .max(2000, "Máximo 2000 caracteres"),
  pedido_accion: z
    .string()
    .max(1000, "Máximo 1000 caracteres")
    .nullable()
    .optional(),
});

export type DetalleReclamacionFormData = z.infer<
  typeof DetalleReclamacionSchema
>;

export const DETALLE_RECLAMACION_DEFAULTS: DetalleReclamacionFormData = {
  tipo_reclamacion: "RECLAMO",
  area_oficina: "",
  descripcion_detalle: "",
  pedido_accion: null,
};
