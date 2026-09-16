import { z } from "zod";

/**
 * Step 1 — Responsable.
 * El responsable ES el usuario logueado (nombres, doc, email, whatsapp y emergencia
 * vienen de la sesión/registro). Aquí solo se pide la promoción y fusión.
 */
export const Step1ResponsableSchema = z.object({
  promocionId: z.string().uuid("Selecciona tu promoción"),
  fusionPromocionId: z
    .string()
    .uuid("Selecciona una promoción válida")
    .optional()
    .nullable(),
});

export type Step1ResponsableData = z.infer<typeof Step1ResponsableSchema>;
