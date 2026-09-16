import { z } from "zod";
import { generos, tipoDocumentos } from "@/infra/drizzle/schema/personas";

export const UserRoleSchema = z.enum([
  "responsable",
  "admin_comite",
  "admin_finanzas",
]);
export type UserRole = z.infer<typeof UserRoleSchema>;

export const TipoDocumentoSchema = z.enum(tipoDocumentos);
export const GeneroSchema = z.enum(generos);

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  tipoDocumento: TipoDocumentoSchema,
  numeroDocumento: z.string(),
  nombres: z.string(),
  apellidos: z.string(),
  genero: GeneroSchema.nullable(),
  telefono: z.string().nullable(),
  rol: UserRoleSchema,
});

export type User = z.infer<typeof UserSchema>;
