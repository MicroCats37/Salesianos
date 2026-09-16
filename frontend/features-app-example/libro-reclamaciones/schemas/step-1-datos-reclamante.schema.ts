import { z } from "zod";

// ── Step 1: Datos del Reclamante ─────────────────────────────────────────────

export const DatosReclamanteSchema = z.object({
  nombre_completo: z
    .string()
    .min(1, "El nombre completo es requerido")
    .max(200, "Máximo 200 caracteres"),
  domicilio: z
    .string()
    .min(1, "El domicilio es requerido")
    .max(300, "Máximo 300 caracteres"),
  tipo_documento: z.enum(["DNI", "CE"], {
    message: "Selecciona un tipo de documento",
  }),
  numero_documento: z
    .string()
    .min(8, "El número de documento debe tener al menos 8 dígitos")
    .max(15, "Máximo 15 caracteres"),
  telefono: z
    .string()
    .min(6, "Mínimo 6 dígitos")
    .max(15, "Máximo 15 caracteres")
    .nullable()
    .optional(),
  email: z
    .string()
    .email("Ingresa un correo electrónico válido")
    .max(255, "Máximo 255 caracteres")
    .nullable()
    .optional(),
});

export type DatosReclamanteFormData = z.infer<typeof DatosReclamanteSchema>;

export const DATOS_RECLAMANTE_DEFAULTS: DatosReclamanteFormData = {
  nombre_completo: "",
  domicilio: "",
  tipo_documento: "DNI",
  numero_documento: "",
  telefono: null,
  email: null,
};
