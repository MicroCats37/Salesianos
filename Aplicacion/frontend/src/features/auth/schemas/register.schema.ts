import { z } from "zod";
import type { TipoDocumento } from "../constants/tipo-aceptacion";

// ── Helpers ────────────────────────────────────────────────────────────────────

/**
 * Validation rules per document type.
 * DNI = 8 digits, CE = 9 digits, PAS = min 4 alphanumeric (normalized to uppercase).
 */
export function buildNumeroDocumentoValidator(tipo: TipoDocumento) {
  if (tipo === "DNI") {
    return z
      .string()
      .regex(/^\d{8}$/, "DNI debe contener exactamente 8 dígitos");
  }
  if (tipo === "CE") {
    return z
      .string()
      .regex(/^\d{9}$/, "CE debe contener exactamente 9 dígitos");
  }
  // PAS
  return z
    .string()
    .regex(
      /^[A-Za-z0-9]{4,}$/,
      "PAS debe tener mínimo 4 caracteres alfanuméricos",
    )
    .transform((v) => v.toUpperCase());
}

/**
 * RegisterFormSchema — mirrors RegisterIn (backend).
 * - password and confirmPassword must match
 * - acceptedBases must be explicitly true
 * - numeroDocumento format depends on tipoDocumento
 */
export const RegisterFormSchema = z
  .object({
    email: z
      .string()
      .min(1, "Email requerido")
      .max(120, "Máximo 120 caracteres")
      .email("Email inválido"),

    password: z
      .string()
      .min(8, "Mínimo 8 caracteres")
      .max(120, "Máximo 120 caracteres"),

    confirmPassword: z.string().min(1, "Confirmación requerida"),

    tipoDocumento: z.enum(["DNI", "CE", "PAS"] as const, {
      error: "Tipo de documento requerido",
    }),

    numeroDocumento: z.string().min(1, "Número de documento requerido"),

    nombres: z
      .string()
      .min(1, "Nombres requeridos")
      .max(120, "Máximo 120 caracteres"),

    apellidos: z
      .string()
      .min(1, "Apellidos requeridos")
      .max(120, "Máximo 120 caracteres"),

    genero: z.enum(["M", "F"] as const, {
      error: "Género requerido",
    }),

    telefono: z
      .string()
      .regex(/^\d{9}$/, "Teléfono debe tener exactamente 9 dígitos")
      .nullable()
      .transform((v) => (v === "" ? null : v))
      .optional(),

    whatsapp: z
      .string()
      .regex(/^\d{9}$/, "WhatsApp debe tener exactamente 9 dígitos")
      .nullable()
      .transform((v) => (v === "" ? null : v))
      .optional(),

    contactoEmergenciaNombre: z
      .string()
      .max(120, "Máximo 120 caracteres")
      .nullable()
      .transform((v) => (v === "" ? null : v))
      .optional(),

    contactoEmergenciaTelefono: z
      .string()
      .regex(
        /^\d{9}$/,
        "Teléfono de emergencia debe tener exactamente 9 dígitos",
      )
      .nullable()
      .transform((v) => (v === "" ? null : v))
      .optional(),

    /** Must be explicitly true — backend rejects if false */
    acceptedBases: z.literal(true, {
      error: "Debes aceptar las bases del evento",
    }),
  })
  .strict()
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
  })
  .superRefine((data, ctx) => {
    const validator = buildNumeroDocumentoValidator(data.tipoDocumento);
    const result = validator.safeParse(data.numeroDocumento);
    if (!result.success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          result.error.issues[0]?.message ?? "Número de documento inválido",
        path: ["numeroDocumento"],
      });
    }
  });

export type RegisterFormData = z.infer<typeof RegisterFormSchema>;

/**
 * RegisterResponse — mirrors RegisterOut (backend).
 */
export interface RegisterResponse {
  access_token: string;
  refresh_token: string;
  expires_at: string;
  user: {
    id: string;
    username: string;
    email: string;
    is_staff: boolean;
    is_superuser: boolean;
    persona_id: string | null;
  };
}

/**
 * The Zod mirror of the `user` of the registration (`SesionUsuarioOut`).
 *
 * Owner: `Aplicacion/backend/modules/usuarios/presentation/schemas/auth_schemas.py`
 * (`LoginTokenOut.user`).
 * Route: `POST /api/auth/register` — REGISTERED in
 * `Aplicacion/backend/config/api.py` (`AuthController`).
 *
 * The wrapper is LOOSE on purpose: the presenter publishes MORE facts than the
 * ones the form needs (`rol`, `nombres`, `capacidades`) and they travel in the
 * cookie of the session. A strict mirror would DROP them and the shell would
 * paint a session without role.
 *
 * `email` is NOT nullable HERE: the account is CREATED with an email (the input
 * of the route requires it), so the presenter always publishes it. The generic
 * session (`GET /auth/me`) is the one whose email may be null, and it has its
 * own mirror (`features/auth/schemas/sesion.schema.ts`).
 */
export const RegisterUserSchema = z.looseObject({
  id: z.string(),
  username: z.string(),
  email: z.string(),
  is_staff: z.boolean(),
  is_superuser: z.boolean(),
  persona_id: z.string().nullable(),
});

/**
 * The Zod mirror of the answer of the registration (`LoginTokenOut`).
 *
 * It is the SAME wrapper that the login publishes: the high of an account
 * opens its session.
 */
export const RegisterResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  expires_at: z.string(),
  user: RegisterUserSchema,
});
