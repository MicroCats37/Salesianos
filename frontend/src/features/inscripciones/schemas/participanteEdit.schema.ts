import { z } from "zod";

/**
 * Schema de edición de un participante dentro de una inscripción.
 *
 * Permite editar: rol, talla_camiseta, seguro y notas.
 * NO permite editar identidad ni declaraciones de aceptaciones.
 *
 * NOTE: Backend uses single-char rol values (J, D) and talla_camiseta (correct spelling).
 */
export const ROLES_PERMITIDOS = ["J", "D"] as const;
export const TALLES_PERMITIDOS = ["XS", "S", "M", "L", "XL", "XXL"] as const;
export const NOTAS_MAX_LENGTH = 500;

const emptyToUndefined = (v: unknown) =>
  typeof v === "string" && v.trim() === "" ? undefined : v;

export const EditarParticipanteSchema = z
  .object({
    rol: z.preprocess(
      emptyToUndefined,
      z.string({ error: "Rol requerido" }).min(1, "Rol requerido"),
    ),
    talla_camiseta: z.preprocess(emptyToUndefined, z.string().optional()),
    aseguradora_nombre: z.preprocess(emptyToUndefined, z.string().optional()),
    aseguradora_numero_poliza: z.preprocess(
      emptyToUndefined,
      z.string().optional(),
    ),
    notas: z.preprocess(
      emptyToUndefined,
      z
        .string()
        .max(
          NOTAS_MAX_LENGTH,
          `Las notas no pueden superar los ${NOTAS_MAX_LENGTH} caracteres`,
        )
        .optional(),
    ),
  })
  .superRefine((data, ctx) => {
    if (
      !ROLES_PERMITIDOS.includes(data.rol as (typeof ROLES_PERMITIDOS)[number])
    ) {
      ctx.addIssue({
        path: ["rol"],
        message: `Rol debe ser uno de: ${ROLES_PERMITIDOS.join(", ")}`,
        code: "custom",
      });
    }
    if (
      data.talla_camiseta &&
      !TALLES_PERMITIDOS.includes(
        data.talla_camiseta as (typeof TALLES_PERMITIDOS)[number],
      )
    ) {
      ctx.addIssue({
        path: ["talla_camiseta"],
        message: `Talle inválido. Use uno de: ${TALLES_PERMITIDOS.join(", ")}`,
        code: "custom",
      });
    }
  });

export type EditarParticipanteFormData = z.infer<
  typeof EditarParticipanteSchema
>;
