import { z } from "zod";

/**
 * The closed vocabulary of the civil document types.
 *
 * It is the vocabulary of the backend
 * (`Aplicacion/backend/modules/usuarios/domain/constants.py`) and the same
 * one the registration form of the product already uses
 * (`features/auth/schemas/register.schema.ts`). It is DECLARED here, not
 * derived: the backend owns which documents exist.
 */
export const TIPOS_DOCUMENTO = ["DNI", "CE", "PAS"] as const;

/**
 * The client-side schema of the buyer form.
 *
 * It is NOT a wire mirror: it validates what the person typed before the
 * request leaves the browser. The exact Zod mirror of the presenter lives in
 * `pase.schema.ts` (`ComprarPaseIn`), and the mapping between the two lives
 * in `utils/pase.payload.utils.ts`.
 *
 * The truth lives in Zod (`contract/smart.md` §5.1): the component never
 * decides on its own whether a value is acceptable.
 *
 * The schema validates the FORM only. The quantity limits, the price and the
 * stock are rules of the domain and the server rejects them with its own
 * codes (`CANTIDAD_INVALIDA`, `PEDIDO_CANTIDAD_INVALIDA`).
 *
 * The maximum lengths ARE the ones of the wire (`ComprarPaseIn`): they catch
 * a value the server would reject with a 422 before it leaves the browser,
 * and they give the person a message attached to the field.
 */
export const CompradorPaseSchema = z.object({
  tipoDocumento: z.enum(TIPOS_DOCUMENTO, {
    error: "Elige el tipo de documento.",
  }),
  numeroDocumento: z
    .string()
    .trim()
    .min(1, "Escribe el número de documento del comprador.")
    .max(20, "El número de documento es demasiado largo."),
  nombres: z
    .string()
    .trim()
    .min(1, "Escribe los nombres del comprador.")
    .max(255, "Los nombres son demasiado largos."),
  apellidos: z
    .string()
    .trim()
    .max(255, "Los apellidos son demasiado largos."),
  contactoEmail: z
    .string()
    .trim()
    .max(255, "El correo es demasiado largo.")
    .refine(
      (valor) => valor.length === 0 || z.email().safeParse(valor).success,
      "Ese correo no tiene un formato válido.",
    ),
});

export type CompradorPaseData = z.infer<typeof CompradorPaseSchema>;

/**
 * The client-side schema of the assignment of a pass to a person.
 *
 * It is NOT a wire mirror either: it validates what the person typed before
 * the request leaves the browser.
 */
export const AsignacionPaseSchema = z.object({
  tipoDocumento: z.enum(TIPOS_DOCUMENTO, {
    error: "Elige el tipo de documento.",
  }),
  numeroDocumento: z
    .string()
    .trim()
    .min(1, "Escribe el número de documento de la persona.")
    .max(20, "El número de documento es demasiado largo."),
  nombres: z
    .string()
    .trim()
    .min(1, "Escribe los nombres de la persona.")
    .max(255, "Los nombres son demasiado largos."),
  apellidos: z
    .string()
    .trim()
    .max(255, "Los apellidos son demasiado largos."),
  motivo: z.string().trim().max(500, "El motivo es demasiado largo."),
});

export type AsignacionPaseData = z.infer<typeof AsignacionPaseSchema>;
