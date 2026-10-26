import { z } from "zod";

export const TipoDocumentoEnum = z.enum(["DNI", "CE", "PAS"]);
export const GeneroEnum = z.enum(["M", "F"]);

export const DNI_REGEX = /^\d{8}$/;
export const CE_REGEX = /^\d{9}$/;
export const PAS_REGEX = /^[A-Za-z0-9]{4,}$/;
export const PHONE_REGEX = /^\d{9}$/;

/** Preprocess: empty string `""` becomes `undefined` so optional fields skip validation. */
const emptyToUndefined = (v: unknown) =>
  typeof v === "string" && v.trim() === "" ? undefined : v;

/**
 * Schema del formulario de participante.
 *
 * - Validación por tipo de documento y formatos se concentran en `superRefine`
 *   para mantener la intención de cross-field y mensajes claros.
 * - `telefono` y `whatsapp` son OPCIONALES: si están vacíos, no se validan;
 *   si tienen valor, deben ser exactamente 9 dígitos.
 * - `talla_camiseta` opcional (backend field name).
 * - `aseguradora_nombre` y `aseguradora_numero_poliza` opcionales.
 * - `notas` opcional, hasta 500 caracteres (alergias, observaciones, etc.).
 * - `rol` default "J" (backend uses single-char values: J=Jugador, D=Delegado).
 */
export const NOTAS_MAX_LENGTH = 500;
export const ASEGURADORAS_PERU = [
  { value: "RIMAC", label: "RIMAC" },
  { value: "PACIFICO", label: "Pacífico" },
  { value: "MAPFRE", label: "MAPFRE" },
  { value: "LA_POSITIVA", label: "La Positiva" },
  { value: "SANITAS", label: "Sanitas" },
  { value: "ESSALUD", label: "Essalud" },
  { value: "SIS", label: "SIS" },
  { value: "OTRO", label: "Otro" },
] as const;

export const ParticipanteSchema = z
  .object({
    tipoDocumento: TipoDocumentoEnum,
    numeroDocumento: z.string().min(1, "Número de documento requerido"),
    nombres: z.string().min(1, "Nombres requeridos").max(120),
    apellidos: z.string().min(1, "Apellidos requeridos").max(120),
    genero: GeneroEnum,
    telefono: z.preprocess(
      emptyToUndefined,
      z
        .string()
        .regex(PHONE_REGEX, "Teléfono debe tener exactamente 9 dígitos")
        .optional(),
    ),
    whatsapp: z.preprocess(
      emptyToUndefined,
      z
        .string()
        .regex(PHONE_REGEX, "WhatsApp debe tener exactamente 9 dígitos")
        .optional(),
    ),
    rol: z.string().default("J"),
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
    // ── Document number format by doc type ─────────────────────────────
    if (data.tipoDocumento === "DNI") {
      if (!DNI_REGEX.test(data.numeroDocumento)) {
        ctx.addIssue({
          path: ["numeroDocumento"],
          message: "DNI debe contener exactamente 8 dígitos",
          code: "custom",
        });
      }
    } else if (data.tipoDocumento === "CE") {
      if (!CE_REGEX.test(data.numeroDocumento)) {
        ctx.addIssue({
          path: ["numeroDocumento"],
          message: "CE debe contener exactamente 9 dígitos",
          code: "custom",
        });
      }
    } else if (data.tipoDocumento === "PAS") {
      if (!PAS_REGEX.test(data.numeroDocumento)) {
        ctx.addIssue({
          path: ["numeroDocumento"],
          message: "Pasaporte debe tener mínimo 4 caracteres alfanuméricos",
          code: "custom",
        });
      }
    }

    // ── Optional phone format ──────────────────────────────────────────
    if (data.telefono && !PHONE_REGEX.test(data.telefono)) {
      ctx.addIssue({
        path: ["telefono"],
        message: "Teléfono debe tener exactamente 9 dígitos",
        code: "custom",
      });
    }
    if (data.whatsapp && !PHONE_REGEX.test(data.whatsapp)) {
      ctx.addIssue({
        path: ["whatsapp"],
        message: "WhatsApp debe tener exactamente 9 dígitos",
        code: "custom",
      });
    }
  });

export type ParticipanteFormData = z.infer<typeof ParticipanteSchema>;
export type ParticipanteFormInput = z.input<typeof ParticipanteSchema>;
