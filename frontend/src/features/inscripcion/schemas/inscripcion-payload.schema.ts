import { z } from "zod";
import { DeportistaWizardSchema } from "./step2-equipo.schema";

/**
 * Payload completo que se envía al Server Action createInscripcionAction.
 * Coincide con CreateInscripcionSchema en src/app/actions/inscripcion/create.ts.
 */
export const InscripcionPayloadSchema = z.object({
  userId: z.string().uuid(),
  promocionId: z.string().uuid("Debes seleccionar una promoción"),
  fusionPromocionId: z.string().uuid().optional().nullable(),
  basesId: z.string().uuid(),
  paqueteMonto: z.number().positive(),
  teamName: z.string().min(1, "Ingresa el nombre del equipo").max(120),
  acceptedBases: z
    .boolean()
    .refine((val) => val === true, { message: "Debes aceptar las bases" }),
  fitnessDeclaration: z.boolean().refine((val) => val === true, {
    message: "Debes confirmar la aptitud física",
  }),
  imageConsent: z.boolean().refine((val) => val === true, {
    message: "Debes dar consentimiento de imagen",
  }),
  deportistas: z
    .array(DeportistaWizardSchema)
    .min(1, "Debes agregar al menos un deportista"),
});

export type InscripcionPayload = z.infer<typeof InscripcionPayloadSchema>;
