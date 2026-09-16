import { z } from "zod";

// ── Step 2: Bien Reclamado ────────────────────────────────────────────────────

export const BienReclamadoSchema = z.object({
  tipo_bien: z.enum(["PRODUCTO", "SERVICIO"], {
    message: "Selecciona el tipo de bien contratado",
  }),
  descripcion_bien: z
    .string()
    .min(1, "La descripción es requerida")
    .max(500, "Máximo 500 caracteres"),
});

export type BienReclamadoFormData = z.infer<typeof BienReclamadoSchema>;

export const BIEN_RECLAMADO_DEFAULTS: BienReclamadoFormData = {
  tipo_bien: "SERVICIO",
  descripcion_bien: "",
};
