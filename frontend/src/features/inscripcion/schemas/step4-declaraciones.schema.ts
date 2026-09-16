import { z } from "zod";

/**
 * Step 4 — Declaraciones.
 * Checkboxes finales requeridos antes de enviar la solicitud.
 */
export const Step4DeclaracionesSchema = z.object({
  fitnessDeclaration: z.boolean().refine((v) => v === true, {
    message: "Debes confirmar la declaración de aptitud física",
  }),
  imageConsent: z.boolean().refine((v) => v === true, {
    message: "Debes dar consentimiento de uso de imagen",
  }),
  acceptedBases: z.boolean().refine((v) => v === true, {
    message: "Debes aceptar las bases oficiales",
  }),
});

export type Step4DeclaracionesData = z.infer<typeof Step4DeclaracionesSchema>;
