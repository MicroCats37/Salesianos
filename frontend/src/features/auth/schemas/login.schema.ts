import { z } from "zod";

/**
 * LoginUsernameFormSchema — requires username + password.
 * Routes to: POST /api/auth/login/username
 */
export const LoginUsernameFormSchema = z.object({
  username: z
    .string()
    .min(1, "Usuario requerido")
    .max(120, "Máximo 120 caracteres"),
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginUsernameFormData = z.infer<typeof LoginUsernameFormSchema>;

/**
 * LoginDniFormSchema — requires DNI (8 digits) + password.
 * Routes to: POST /api/auth/login/dni
 */
export const LoginDniFormSchema = z.object({
  dni: z
    .string()
    .length(8, "DNI debe tener exactamente 8 dígitos")
    .regex(/^\d{8}$/, "DNI debe contener solo números"),
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginDniFormData = z.infer<typeof LoginDniFormSchema>;

/**
 * LoginEmailFormSchema — requires email + password.
 * Routes to: POST /api/auth/login/email
 */
export const LoginEmailFormSchema = z.object({
  email: z
    .string()
    .min(1, "Email requerido")
    .email("Email inválido"),
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginEmailFormData = z.infer<typeof LoginEmailFormSchema>;
