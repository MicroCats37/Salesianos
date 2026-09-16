// features/tramites/schemas/crearSolicitud.schema.ts
// Schema Zod unificado para el formulario de creación de solicitudes (SolicitudHibridaCreateIn).
// Todos los campos siempre visibles — validación con .nullable() para no-aplicables.

import { z } from "zod";

// ── Enums ────────────────────────────────────────────────────────────────────────

export const TIPO_PERSONA = ["NATURAL", "JURIDICA", "COLEGIADO"] as const;
export type TipoPersona = (typeof TIPO_PERSONA)[number];

export const TIPO_PARTICIPACION = ["PRINCIPAL", "ADJUNTA"] as const;
export type TipoParticipacion = (typeof TIPO_PARTICIPACION)[number];

export const TIPO_ARCHIVO_ENUM = ["PRINCIPAL", "ANEXO"] as const;
export type TipoArchivoEnum = (typeof TIPO_ARCHIVO_ENUM)[number];

export const PRIORIDAD = ["BAJA", "MEDIA", "ALTA", "URGENTE"] as const;
export type Prioridad = (typeof PRIORIDAD)[number];

// ── Archivo item (usado por InputFileCollection) ─────────────────────────────────

export const ArchivoItemSchema = z.object({
  tipo_archivo: z.enum(TIPO_ARCHIVO_ENUM),
  nombre_original: z.string(),
  descripcion: z.string().nullable().optional(),
  file: z.instanceof(File),
});

export type ArchivoItemData = z.infer<typeof ArchivoItemSchema>;

// ── Validaciones auxiliares (regex) ──────────────────────────────────────────────

/** DNI: 8 dígitos exactos */
const DNI_REGEX = /^\d{8}$/;
/** RUC: 11 dígitos exactos */
const RUC_REGEX = /^\d{11}$/;
/** CIP: hasta 6 dígitos */
const CIP_REGEX = /^\d{1,6}$/;
/** Teléfono peruano: 9 dígitos, opcional prefijo +51 */
const TELEFONO_REGEX = /^\+?\d{6,12}$/;

// ── Schema unificado —flattened─ ─────────────────────────────────────────────────

/**
 * Schema unificado para SolicitudHibridaCreateIn.
 * Campos del expediente (tipo_persona, dni, ruc, cip, nombres, apellidos,
 * razon_social, correo, telefono, tipo_documento, numero_documento, numero_folios,
 * asunto, observaciones) están al mismo nivel que prioridad/areas_distribucion.
 *
 * El handleSubmit del formulario transforma esta estructura plana a la nested
 * que espera el backend: { prioridad, observacion, areas_distribucion, expediente: {...}, antecedentes: [] }
 */
export const CrearSolicitudSchema = z.object({
  // ── Expediente / Datos del Solicitante (siempre visibles) ──────────────────
  tipo_persona: z.enum(TIPO_PERSONA, {
    message: "Selecciona un tipo de persona",
  }),

  dni: z
    .string()
    .regex(DNI_REGEX, {
      message: "El DNI debe tener exactamente 8 dígitos",
    })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  ruc: z
    .string()
    .regex(RUC_REGEX, {
      message: "El RUC debe tener exactamente 11 dígitos",
    })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  cip: z
    .string()
    .regex(CIP_REGEX, {
      message: "El CIP debe tener hasta 6 dígitos",
    })
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  razon_social: z
    .string()
    .max(255, "La razón social no puede exceder 255 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  nombres: z
    .string()
    .max(150, "Los nombres no pueden exceder 150 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  apellidos: z
    .string()
    .max(150, "Los apellidos no pueden exceder 150 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  correo: z
    .string()
    .email("Ingresa un correo electrónico válido")
    .max(255, "El correo no puede exceder 255 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  telefono: z
    .string()
    .regex(TELEFONO_REGEX, {
      message: "El teléfono debe tener entre 6 y 12 dígitos",
    })
    .max(12, "El teléfono no puede exceder 12 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  tipo_documento_id: z
    .string()
    .uuid({ message: "Selecciona un tipo de documento" })
    .nullable()
    .optional(),

  numero_documento: z
    .string()
    .max(50, "El número de documento no puede exceder 50 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  numero_folios: z
    .number({ message: "Los folios deben ser un número" })
    .int("Los folios deben ser un número entero")
    .min(0, "Los folios no pueden ser negativos")
    .default(0),

  asunto: z
    .string()
    .min(1, "El asunto es requerido")
    .max(500, "El asunto no puede exceder 500 caracteres"),

  observaciones: z
    .string()
    .max(1000, "Las observaciones no pueden exceder 1000 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),

  // ── Archivos (siempre visible — InputFileCollection) ───────────────────────
  archivos: z.array(ArchivoItemSchema).default([]),

  // ── Áreas (siempre visible — InputAreaDistribution) ────────────────────────
  areas_distribucion: z
    .array(
      z.object({
        area_id: z.string().uuid({ message: "Selecciona un área válida" }),
        tipo_participacion: z.enum(TIPO_PARTICIPACION, {
          message: "Selecciona un tipo de participación",
        }),
        observacion: z
          .string()
          .max(255, "La observación no puede exceder 255 caracteres")
          .nullable()
          .optional()
          .or(z.literal("").transform(() => null)),
      }),
    )
    .min(1, "Debes asignar al menos un área a la solicitud"),

  // ── Meta ──────────────────────────────────────────────────────────────────
  prioridad: z
    .enum(PRIORIDAD, {
      message: "Selecciona una prioridad",
    })
    .default("MEDIA"),

  observacion: z
    .string()
    .max(1000, "La observación no puede exceder 1000 caracteres")
    .nullable()
    .optional()
    .or(z.literal("").transform(() => null)),
});

export type CrearSolicitudData = z.infer<typeof CrearSolicitudSchema>;

// ── Helpers ─────────────────────────────────────────────────────────────────────

/** Valores por defecto para el formulario */
export const CREAR_SOLICITUD_DEFAULT: Partial<CrearSolicitudData> = {
  tipo_persona: "NATURAL",
  numero_folios: 0,
  prioridad: "MEDIA",
  areas_distribucion: [],
  archivos: [],
  dni: null,
  ruc: null,
  cip: null,
  nombres: null,
  apellidos: null,
  razon_social: null,
  correo: null,
  telefono: null,
  tipo_documento_id: null,
  numero_documento: null,
  observaciones: null,
  observacion: null,
};
