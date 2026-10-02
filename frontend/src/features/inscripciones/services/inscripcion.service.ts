"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";
import type { InscripcionBackendPayload } from "../schemas/inscripcion.schema";

// ── Response Types ────────────────────────────────────────────────────────────

export interface InscripcionOut {
  id: string;
  evento_id: string;
  responsable_id: string;
  paquete_id: string;
  estado: string;
  created_at: string;
  evento_nombre?: string | null;
  paquete_nombre?: string | null;
  promocion_nombre?: string | null;
  fusion_promocion_nombre?: string | null;
  cantidad_equipos?: number;
  cantidad_participantes?: number;
}

export interface InscripcionResponse {
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

// ── API Function ────────────────────────────────────────────────────────────────

export async function createInscripcion(
  payload: InscripcionBackendPayload,
): Promise<ApiResponse<InscripcionOut>> {
  const { data } = await api.post<ApiResponse<InscripcionOut>>(
    "/inscripciones/",
    payload,
  );
  return data;
}

export async function getMisInscripciones(): Promise<
  ApiResponse<InscripcionOut[]>
> {
  const { data } =
    await api.get<ApiResponse<InscripcionOut[]>>("/inscripciones/");
  return data;
}

// ── Detail Types ────────────────────────────────────────────────────────────────

export interface PersonaResumen {
  id: string;
  nombres: string;
  apellidos: string;
  numero_documento: string;
  aseguradora_nombre?: string | null;
  aseguradora_numero_poliza?: string | null;
  contacto_emergencia_nombre?: string | null;
  contacto_emergencia_telefono?: string | null;
}

export interface DisciplinaResumen {
  id: string;
  nombre: string;
  sigla: string;
}

export interface CategoriaResumen {
  id: string;
  nombre: string;
}

export interface ParticipanteOut {
  id: string;
  participacion_id: string;
  equipo_id: string;
  rol: string;
  talle_camiseta: string | null;
  notas: string | null;
  persona: PersonaResumen;
  acepto_bases: boolean;
  acepto_aptitud_fisica: boolean;
  acepto_imagen: boolean;
}

export interface ParticipacionOut {
  id: string;
  evento_id: string;
  disciplina_id: string;
  persona_id: string;
  equipo_id: string;
  persona: PersonaResumen;
  disciplina: DisciplinaResumen;
}

export interface EquipoDetalleOut {
  id: string;
  inscripcion_id: string;
  disciplina_id: string;
  categoria_id: string | null;
  nombre: string;
  disciplina: DisciplinaResumen;
  categoria: CategoriaResumen | null;
  participantes: ParticipanteOut[];
}

export interface PromocionResumenOut {
  id: string;
  anio: number;
  nombre: string;
}

export interface DelegadoOut {
  id: string;
  inscripcion_id: string;
  persona_id: string;
  persona_nombre: string | null;
  persona_numero_documento: string | null;
}

export interface EventoResumenOut {
  id: string;
  nombre: string;
}

export interface PaqueteResumenOut {
  id: string;
  nombre: string;
}

export interface InscripcionDetalleOut {
  id: string;
  evento_id: string;
  responsable_id: string;
  paquete_id: string;
  promocion: PromocionResumenOut;
  fusion_promocion: PromocionResumenOut | null;
  estado: string;
  observacion: string | null;
  created_at: string;
  evento: EventoResumenOut;
  paquete: PaqueteResumenOut;
  equipos: EquipoDetalleOut[];
  delegado: DelegadoOut | null;
  responsable_acepto_bases: boolean;
  responsable_acepto_aptitud_fisica: boolean;
  responsable_acepto_imagen: boolean;
}

export async function getInscripcionDetalle(
  id: string,
): Promise<ApiResponse<InscripcionDetalleOut>> {
  const { data } = await api.get<ApiResponse<InscripcionDetalleOut>>(
    `/inscripciones/${id}`,
  );
  return data;
}

// ── Add Participants to Existing Equipo ────────────────────────────────────────

export interface AgregarParticipantesPayload {
  participantes: Array<{
    tipoDocumento?: "DNI" | "CE" | "PAS";
    numeroDocumento?: string;
    nombres?: string;
    apellidos?: string;
    genero?: "M" | "F";
    telefono?: string | null;
    whatsapp?: string | null;
    persona_id?: string;
    rol?: string;
    talle_camiseta?: string | null;
    aseguradora_nombre?: string | null;
    aseguradora_numero_poliza?: string | null;
    notas?: string | null;
    acepto_bases?: boolean;
    acepto_aptitud_fisica?: boolean;
    acepto_imagen?: boolean;
  }>;
}

export interface AgregarParticipantesRespuesta {
  participantes: ParticipanteOut[];
}

export interface AgregarParticipanteRespuesta {
  participante: ParticipanteOut;
}

export async function agregarParticipantesAEquipo(
  inscripcionId: string,
  equipoId: string,
  payload: AgregarParticipantesPayload,
): Promise<ApiResponse<AgregarParticipantesRespuesta>> {
  const { data } = await api.patch<ApiResponse<AgregarParticipantesRespuesta>>(
    `/inscripciones/${inscripcionId}/equipos/${equipoId}/participantes`,
    payload,
  );
  return data;
}

// ── Edit / Delete / Move participant ────────────────────────────────────────────

export interface EditarParticipantePayload {
  rol?: string;
  talle_camiseta?: string | null;
  aseguradora_nombre?: string | null;
  aseguradora_numero_poliza?: string | null;
  notas?: string | null;
  acepto_bases?: boolean;
  acepto_aptitud_fisica?: boolean;
  acepto_imagen?: boolean;
}

export async function editarParticipante(
  inscripcionId: string,
  participanteId: string,
  payload: EditarParticipantePayload,
): Promise<ApiResponse<ParticipanteOut>> {
  const { data } = await api.patch<ApiResponse<ParticipanteOut>>(
    `/inscripciones/${inscripcionId}/participantes/${participanteId}`,
    payload,
  );
  return data;
}

export async function eliminarParticipante(
  inscripcionId: string,
  participanteId: string,
): Promise<ApiResponse<{ participante_id: string }>> {
  const { data } = await api.delete<ApiResponse<{ participante_id: string }>>(
    `/inscripciones/${inscripcionId}/participantes/${participanteId}`,
  );
  return data;
}

export interface MoverParticipantePayload {
  equipo_destino_id: string;
}

export async function moverParticipante(
  inscripcionId: string,
  participanteId: string,
  payload: MoverParticipantePayload,
): Promise<ApiResponse<ParticipanteOut>> {
  const { data } = await api.patch<ApiResponse<ParticipanteOut>>(
    `/inscripciones/${inscripcionId}/participantes/${participanteId}/mover`,
    payload,
  );
  return data;
}

// ── DNI Lookup ────────────────────────────────────────────────────────────────

export interface DocumentoConsultaData {
  tipo_documento: string;
  numero_documento: string;
  razon_social: string;
}

export async function consultarDocumento(
  documento: string,
): Promise<ApiResponse<DocumentoConsultaData>> {
  const { data } = await api.get<ApiResponse<DocumentoConsultaData>>(
    `/personas/busqueda/${documento}`,
  );
  return data;
}
