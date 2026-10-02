import { z } from "zod";
import { ParticipanteSchema } from "./participante.schema";

export type { ParticipanteFormData } from "./participante.schema";
export {
  DNI_REGEX,
  CE_REGEX,
  PAS_REGEX,
  PHONE_REGEX,
  TipoDocumentoEnum,
  GeneroEnum,
} from "./participante.schema";

// ── Equipo Schema ─────────────────────────────────────────────────────────────

export const EquipoSchema = z.object({
  disciplina_id: z.string().min(1, "Selecciona una disciplina"),
  categoria_id: z.string().nullable().optional(),
  nombre: z.string().min(1, "Nombre del equipo requerido").max(120),
  // Draft inscriptions may be created without participants. Roster min/max is
  // validated later by the backend when the inscription is reviewed/confirmed.
  participantes: z.array(ParticipanteSchema),
});

export type EquipoFormData = z.infer<typeof EquipoSchema>;

// ── Main Inscripcion Schema ────────────────────────────────────────────────────

export const InscripcionFormSchema = z.object({
  // Catalog IDs (evento is NOT a client input — resolved server-side)
  paquete_id: z.string().min(1, "Selecciona un paquete"),
  promocion_id: z.string().min(1, "Selecciona tu promoción"),
  fusion_promocion_id: z.string().nullable().optional(),

  // Equipos — array (paquete puede incluir varias disciplinas)
  equipos: z.array(EquipoSchema).min(1, "Agrega al menos un equipo"),

  // Declarations
  acceptedBases: z.literal(true, {
    error: "Debes aceptar las bases del evento",
  }),
  fitnessDeclaration: z.literal(true, {
    error: "Debes declarar tu aptitud física",
  }),
  imageConsent: z.literal(true, {
    error: "Debes dar tu consentimiento de imagen",
  }),
});

export type InscripcionFormData = z.infer<typeof InscripcionFormSchema>;

// ── Backend Payload Mapping ─────────────────────────────────────────────────────

/**
 * Maps frontend camelCase to the backend expected snake_case payload.
 * Backend InscripcionCreateIn accepts aliases for booleans (acceptedBases, etc.)
 * but requires snake_case IDs.
 *
 * NOTE: `evento_id` is intentionally NOT in this payload. The active event is
 * resolved server-side from `settings.EVENTO_ACTIVO_NOMBRE`.
 */
export interface InscripcionBackendPayload {
  paquete_id: string;
  promocion_id: string;
  fusion_promocion_id?: string | null;
  equipos: Array<{
    disciplina_id: string;
    categoria_id: string | null;
    nombre: string;
    participantes: Array<{
      tipoDocumento: "DNI" | "CE" | "PAS";
      numeroDocumento: string;
      nombres: string;
      apellidos: string;
      genero: "M" | "F";
      telefono: string | null;
      whatsapp: string | null;
      rol: string;
      talle_camiseta: string | null;
      notas: string | null;
    }>;
  }>;
  acceptedBases: boolean;
  fitnessDeclaration: boolean;
  imageConsent: boolean;
}

export function toBackendPayload(
  data: InscripcionFormData,
): InscripcionBackendPayload {
  return {
    paquete_id: data.paquete_id,
    promocion_id: data.promocion_id,
    fusion_promocion_id: data.fusion_promocion_id ?? null,
    equipos: data.equipos.map((eq) => ({
      disciplina_id: eq.disciplina_id,
      categoria_id: null,
      nombre: eq.nombre,
      participantes: eq.participantes.map((p) => ({
        tipoDocumento: p.tipoDocumento,
        numeroDocumento: p.numeroDocumento,
        nombres: p.nombres,
        apellidos: p.apellidos,
        genero: p.genero,
        telefono: p.telefono ?? null,
        whatsapp: p.whatsapp ?? null,
        rol: p.rol ?? "JUGADOR",
        talle_camiseta: p.talle_camiseta ?? null,
        notas: p.notas ?? null,
      })),
    })),
    acceptedBases: data.acceptedBases,
    fitnessDeclaration: data.fitnessDeclaration,
    imageConsent: data.imageConsent,
  };
}
