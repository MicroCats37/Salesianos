import { z } from "zod";
import { generos, tipoDocumentos } from "@/infra/drizzle/schema/personas";

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export const RegisterFormSchema = z
  .object({
    email: z
      .string()
      .regex(EMAIL_REGEX, "Email inválido")
      .max(120, "Máximo 120 caracteres"),
    password: z
      .string()
      .min(8, "La contraseña debe tener al menos 8 caracteres")
      .max(120, "Máximo 120 caracteres"),
    confirmPassword: z.string().min(1, "Confirma tu contraseña"),
    /** DB has default('DNI'), form always provides via defaultValues */
    tipoDocumento: z.enum(tipoDocumentos).optional(),
    /** Conditional on tipoDocumento — validated in superRefine */
    numeroDocumento: z.string().optional(),
    nombres: z
      .string()
      .min(1, "Ingresa los nombres")
      .max(120, "Máximo 120 caracteres"),
    apellidos: z
      .string()
      .min(1, "Ingresa los apellidos")
      .max(120, "Máximo 120 caracteres"),
    genero: z.enum(generos).optional().nullable(),
    telefono: z.string().optional().nullable(),
    whatsapp: z.string().optional().nullable(),
    emergencyName: z.string().max(120).optional().nullable(),
    emergencyPhone: z.string().optional().nullable(),
    acceptedBases: z.boolean().refine((v) => v === true, {
      message: "Debes aceptar las bases del evento",
    }),
  })
  .superRefine((data, ctx) => {
    const { tipoDocumento, numeroDocumento } = data;

    // tipoDocumento is optional (DB default handles it), but if provided,
    // numeroDocumento becomes required and must match the format
    if (!tipoDocumento) {
      // No tipo selected — skip document number validation
      return;
    }

    if (!numeroDocumento || numeroDocumento.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Ingresa el número de documento",
        path: ["numeroDocumento"],
      });
      return;
    }

    if (tipoDocumento === "DNI") {
      if (!/^\d{8}$/.test(numeroDocumento)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El DNI debe tener exactamente 8 dígitos numéricos",
          path: ["numeroDocumento"],
        });
      }
    } else if (tipoDocumento === "CE") {
      if (!/^\d{9}$/.test(numeroDocumento)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El CE debe tener exactamente 9 dígitos numéricos",
          path: ["numeroDocumento"],
        });
      }
    } else if (tipoDocumento === "PAS") {
      // PAS/Pasaporte: minimum 4 alphanumeric characters
      if (numeroDocumento.trim().length < 4) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El PAS debe tener al menos 4 caracteres alfanuméricos",
          path: ["numeroDocumento"],
        });
      }
    }
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
  })
  .superRefine((data, ctx) => {
    const { telefono } = data;
    if (!telefono || telefono.trim() === "") return;
    if (!/^\d{9}$/.test(telefono)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El teléfono debe tener exactamente 9 dígitos numéricos",
        path: ["telefono"],
      });
    }
  })
  .superRefine((data, ctx) => {
    const { whatsapp } = data;
    if (!whatsapp || whatsapp.trim() === "") return;
    if (!/^\d{9}$/.test(whatsapp)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El WhatsApp debe tener exactamente 9 dígitos numéricos",
        path: ["whatsapp"],
      });
    }
  })
  .superRefine((data, ctx) => {
    const { emergencyPhone } = data;
    if (!emergencyPhone || emergencyPhone.trim() === "") return;
    if (!/^\d{9}$/.test(emergencyPhone)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          "El teléfono de emergencia debe tener exactamente 9 dígitos numéricos",
        path: ["emergencyPhone"],
      });
    }
  });

export type RegisterFormData = z.infer<typeof RegisterFormSchema>;
