import { z } from "zod";

export type LoginMode = "username" | "dni" | "email";

// ── DNI Validation ────────────────────────────────────────────────────────────

/** Validates Peruvian DNI format: exactly 8 numeric digits */
const DniSchema = z
  .string()
  .min(1, "DNI requerido")
  .regex(/^\d{8}$/, "DNI debe tener exactamente 8 dígitos numéricos");

// ── Username Validation ────────────────────────────────────────────────────────

/** Validates username: min 3 chars, alphanumeric + underscore */
const UsernameSchema = z
  .string()
  .min(3, "Usuario debe tener al menos 3 caracteres")
  .max(120, "Máximo 120 caracteres")
  .regex(/^[a-zA-Z0-9_]+$/, "Solo letras, números y guiones bajos");

// ── Login Schemas ─────────────────────────────────────────────────────────────

/**
 * LoginUsernameFormSchema — requires username + password.
 * Routes to: POST /api/auth/login with { identifier: username, password }
 */
export const LoginUsernameFormSchema = z.object({
  username: UsernameSchema,
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginUsernameFormData = z.infer<typeof LoginUsernameFormSchema>;

/**
 * LoginDniFormSchema — requires dni (8 digits) + password.
 * Routes to: POST /api/auth/login with { identifier: dni, password }
 */
export const LoginDniFormSchema = z.object({
  dni: DniSchema,
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginDniFormData = z.infer<typeof LoginDniFormSchema>;

/**
 * LoginEmailFormSchema — requires email + password.
 * Routes to: POST /api/auth/login with { identifier: email, password }
 */
export const LoginEmailFormSchema = z.object({
  email: z
    .string()
    .min(1, "Email requerido")
    .email("Email inválido")
    .max(120, "Máximo 120 caracteres"),
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginEmailFormData = z.infer<typeof LoginEmailFormSchema>;

/**
 * Legacy single-field login schema (identifier = email or DNI).
 * Kept for backwards compatibility with existing forms.
 */
export const LoginFormSchema = z.object({
  identifier: z
    .string()
    .min(1, "Email o DNI requerido")
    .max(120, "Máximo 120 caracteres"),
  password: z
    .string()
    .min(1, "Contraseña requerida")
    .max(120, "Máximo 120 caracteres"),
});

export type LoginFormData = z.infer<typeof LoginFormSchema>;

// ── Discriminated Union Payload ────────────────────────────────────────────────

export type LoginPayload =
  | LoginUsernameFormData
  | LoginDniFormData
  | LoginEmailFormData;
