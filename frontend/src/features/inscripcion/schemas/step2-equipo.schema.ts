import { z } from "zod";
import {
  AcreditacionTipos,
  DeportistaRoles,
  TallaCamisetas,
} from "@/infra/drizzle/schema/deportistas";
import { generos, tipoDocumentos } from "@/infra/drizzle/schema/personas";

/**
 * Step 2 — Equipo y nómina.
 * teamName + lista de deportistas. Cada deportista puede estar en varias disciplinas
 * (checkboxes) y declara su talla referencial de camiseta.
 */
export const DeportistaWizardSchema = z
  .object({
    tipoDocumento: z.enum(tipoDocumentos, {
      message: "Selecciona el tipo de documento",
    }),
    numeroDocumento: z.string().min(1, "Ingresa el número de documento"),
    nombres: z
      .string()
      .min(1, "Ingresa los nombres del deportista")
      .max(120, "Máximo 120 caracteres"),
    apellidos: z
      .string()
      .min(1, "Ingresa los apellidos del deportista")
      .max(120, "Máximo 120 caracteres"),
    genero: z.enum(generos).optional().nullable(),
    telefono: z.string().optional().nullable(),
    rolDisciplina: z.enum(DeportistaRoles, { message: "Selecciona el rol" }),
    acreditacion: z.enum(AcreditacionTipos, {
      message: "Selecciona el tipo de acreditación",
    }),
    disciplinaIds: z
      .array(z.string().uuid())
      .min(1, "Selecciona al menos una disciplina"),
    shirtSize: z.enum(TallaCamisetas).optional().nullable(),
  })
  .superRefine((data, ctx) => {
    const { tipoDocumento, numeroDocumento } = data;

    if (!numeroDocumento || numeroDocumento.trim() === "") {
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
    } else {
      // PAS: at least 4 alphanumeric characters
      if (numeroDocumento.trim().length < 4) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El PAS debe tener al menos 4 caracteres alfanuméricos",
          path: ["numeroDocumento"],
        });
      }
    }
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
  });

export const Step2EquipoSchema = z.object({
  teamName: z.string().min(1, "Ingresa el nombre del equipo").max(120),
  deportistas: z
    .array(DeportistaWizardSchema)
    .min(1, "Debe registrar al menos un deportista"),
});

export type DeportistaWizardData = z.infer<typeof DeportistaWizardSchema>;
export type Step2EquipoData = z.infer<typeof Step2EquipoSchema>;
