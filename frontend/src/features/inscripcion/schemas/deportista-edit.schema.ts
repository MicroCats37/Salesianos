import { z } from "zod";

/**
 * Schema for add/edit player in the Edit Modal.
 * Uses superRefine for cross-field document validation.
 *
 * Rules:
 * - DNI: exactly 8 numeric digits
 * - CE/PAS: non-empty string, reasonable length
 * - Duplicate document numbers within the modal are caught at submit guard
 */
export const DeportistaEditSchema = z
  .object({
    tipoDocumento: z.enum(["DNI", "CE", "PAS"], {
      message: "Selecciona el tipo de documento",
    }),
    numeroDocumento: z.string().min(1, "El número de documento es requerido"),
    nombres: z
      .string()
      .min(1, "Los nombres son requeridos")
      .max(120, "Máximo 120 caracteres"),
    apellidos: z
      .string()
      .min(1, "Los apellidos son requeridos")
      .max(120, "Máximo 120 caracteres"),
    genero: z.enum(["V", "M"]).optional().nullable(),
    telefono: z.string().optional().nullable(),
    rolDisciplina: z.enum(["Jugador", "Capitán", "Delegado"], {
      message: "Selecciona el rol",
    }),
    acreditacion: z.enum(["Verificación en padrón", "Excepción aprobada"], {
      message: "Selecciona la acreditación",
    }),
    disciplinaIds: z
      .array(z.string())
      .min(1, "Selecciona al menos una disciplina"),
    shirtSize: z.enum(["XS", "S", "M", "L", "XL", "XXL"]).optional().nullable(),
    // Internal id for existing players (undefined for new players)
    id: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    const { tipoDocumento, numeroDocumento } = data;

    if (!numeroDocumento || numeroDocumento.trim() === "") {
      // Base validation handles empty
      return;
    }

    if (tipoDocumento === "DNI") {
      // DNI must be exactly 8 numeric digits
      if (!/^\d{8}$/.test(numeroDocumento)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El DNI debe tener exactamente 8 dígitos numéricos",
          path: ["numeroDocumento"],
        });
      }
    } else if (tipoDocumento === "CE") {
      // CE must be exactly 9 numeric digits
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
          message: `El ${tipoDocumento} debe tener al menos 4 caracteres alfanuméricos`,
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

export type DeportistaEditData = z.infer<typeof DeportistaEditSchema>;

/**
 * Schema for the complete Edit Modal form (team name + deportistas list).
 * Validates that:
 * - Team name is present
 * - At least one deportista exists
 * - No duplicate document numbers within the list
 */
export const InscripcionEditSchema = z
  .object({
    teamName: z
      .string()
      .min(1, "El nombre del equipo es requerido")
      .max(120, "Máximo 120 caracteres"),
    deportistas: z
      .array(DeportistaEditSchema)
      .min(1, "Debe haber al menos un deportista"),
  })
  .superRefine((data, ctx) => {
    const { deportistas } = data;
    if (!deportistas || deportistas.length === 0) return;

    // Check for duplicate document numbers within the modal list
    const seen = new Map<string, number>();
    for (let i = 0; i < deportistas.length; i++) {
      const player = deportistas[i];
      const key = `${player.tipoDocumento}:${player.numeroDocumento}`;
      const existing = seen.get(key);
      if (existing !== undefined) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Documento duplicado: ${player.numeroDocumento} (${player.tipoDocumento}) ya existe en la nómina`,
          path: ["deportistas", existing, "numeroDocumento"],
        });
      }
      seen.set(key, i);
    }
  });

export type InscripcionEditData = z.infer<typeof InscripcionEditSchema>;
