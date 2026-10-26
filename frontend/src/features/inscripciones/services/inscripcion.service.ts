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

// ── Atomic Inscription + Purchase + Teams ────────────────────────────────────────

export interface EquipoParaCrearOut {
  id: string;
  inscripcion_id: string;
  disciplina: DisciplinaResumen;
  categoria: CategoriaResumen | null;
  nombre: string;
  estado: string;
  created_at: string;
}

export interface InscripcionCompletaOut {
  inscripcion_id: string;
  inscripcion_estado: string;
  compra_id: string;
  orden_pago_id: string;
  compra_estado: string;
  cantidad: number;
  precio_unitario: number;
  total: number;
  equipos: EquipoParaCrearOut[];
}

/**
 * Payload for atomic inscription + compra + equipos creation.
 * Uses POST /inscripciones/completa/
 */
export interface InscripcionCompletaPayload {
  evento_id: string;
  paquete_id: string;
  promocion_id: string;
  fusion_promocion_id?: string | null;
  delegado_id?: string | null;
  cantidad: number; // Must be >= paquete.minimo_compra_inicial
  equipos: Array<{
    disciplina_id: string;
    categoria_id?: string | null;
    nombre: string;
  }>;
  estado?: string;
  observacion?: string;
  precio_unitario_cotizado?: number | null; // Optional: triggers server-side price revalidation
  /** Quotation version — metadata, not validated server-side yet. */
  cotizacion_version?: number | null;
}

export async function createInscripcionCompleta(
  payload: InscripcionCompletaPayload,
): Promise<ApiResponse<InscripcionCompletaOut>> {
  const { data } = await api.post<ApiResponse<InscripcionCompletaOut>>(
    "/inscripciones/completa/",
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
  inscripcion_persona_id: string;
  equipo_id: string;
  equipo_nombre: string;
  evento_id: string;
  disciplina: DisciplinaResumen;
  persona: PersonaResumen;
  rol: string;
  talla_camiseta: string | null;
  notas: string | null;
  estado: string;
  created_at: string;
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
  /** Persisted EQUIPO_ACTIVO / EQUIPO_CANCELADO — backward-compat raw value. */
  estado: string;
  /** Persisted team state (alias of ``estado``, explicit name for Phase 2+). */
  estado_equipo: string;
  /** Derived/read-only roster state — "COMPLETO" | "INCOMPLETO", computed by presenter. */
  estado_roster: "COMPLETO" | "INCOMPLETO";
  /** Count of ACTIVA participaciones only. */
  jugadores_registrados: number;
  /** Disciplina.min_jugadores threshold. */
  minimo_deportivo: number;
  /** max(0, minimo_deportivo - jugadores_registrados). */
  faltantes: number;
  participantes: ParticipanteOut[];
}

export interface PromocionResumenOut {
  id: string;
  anio: number;
  nombre: string;
}

export interface DelegadoOut {
  /** ID of the inscripcion. */
  id: string;
  /** ID of the delegated person. */
  persona_id: string;
  /** Full name of the delegated person (flat field from backend). */
  persona_nombre: string | null;
  /** Document number of the delegated person. */
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

export interface PersonaResumen {
  id: string;
  nombre: string;
  numero_documento: string;
}

export interface InscripcionPersonaSummaryOut {
  id: string;
  persona: PersonaResumen;
  estado: string;
}

// ── Phase 2: Summary Types ─────────────────────────────────────────────────────

/** Payment-order summary — mirrors backend `OrdenPagoResumenSchema`. */
export interface OrdenPagoResumenOut {
  id: string;
  numero: string;
  estado: string;
  pagada_en: string | null;
}

/** Commercial purchase summary — mirrors backend `CompraResumenSchema`. */
export interface CompraResumenOut {
  id: string;
  tipo: string; // INICIAL | AMPLIACION
  cantidad: number;
  precio_unitario: number;
  total: number;
  estado: string; // PENDIENTE | PAGADA | CANCELADA
  orden_pago: OrdenPagoResumenOut | null;
}

/** Aggregate payment/commercial summary — mirrors backend `ResumenPagoSchema`. */
export interface ResumenPagoOut {
  total_compras: number;
  total_contratado: number;
  total_pagado: number;
  total_pagado_cantidad: number;
  compras_pendientes: number;
  compras_pagadas: number;
  compras_canceladas: number;
  disponible_pagado: number;
  estado_mensaje: string;
  compras: CompraResumenOut[];
}

/** Aggregate team-roster summary — mirrors backend `ResumenEquiposSchema`. */
export interface ResumenEquiposOut {
  total: number;
  completos: number;
  incompletos: number;
}

/**
 * Distinct people vs roster rows — mirrors backend `ResumenParticipantesSchema`.
 *
 * One paid cup authorises a person in EVERY contracted discipline, so the two
 * numbers differ by design and must never be mixed:
 *
 * - `participaciones` — the ACTIVE roster rows.
 * - `personas` — the DISTINCT people (the ones comparable with the cupos).
 */
export interface ResumenParticipantesOut {
  participaciones: number;
  personas: number;
}

export interface InscripcionDetalleOut {
  id: string;
  evento_id: string;
  evento_nombre: string;
  responsable_id: string;
  responsable_nombre: string;
  paquete_id: string;
  paquete_nombre: string;
  promocion_id: string;
  promocion_nombre: string;
  fusion_promocion_id: string | null;
  /** Delegado ID (null if no delegate set). */
  delegado_id: string | null;
  /** Delegado full name (flat field from backend, not DelegadoOut). */
  delegado_nombre: string | null;
  estado: string;
  observacion: string | null;
  created_at: string;
  equipos: EquipoDetalleOut[];
  /** Roster members — persons registered to this inscription (not per-team). */
  personas: InscripcionPersonaSummaryOut[];
  // Phase 2: aggregate team roster summary
  resumen_equipos: ResumenEquiposOut;
  // Phase 2: aggregate payment/commercial summary
  resumen_pago: ResumenPagoOut;
  // Distinct people vs roster rows — one cup authorises several disciplines.
  resumen_participantes: ResumenParticipantesOut;
}

export async function getInscripcionDetalle(
  id: string,
): Promise<ApiResponse<InscripcionDetalleOut>> {
  const { data } = await api.get<ApiResponse<InscripcionDetalleOut>>(
    `/inscripciones/${id}/detalle`,
  );
  return data;
}

// ── Pool preregistration ──────────────────────────────────────────────────────
//
// The ONLY way to register a participant. It lives in `pool.service.ts`
// (`preregistrarEnPool()`) because the preregistration is submitted WITHOUT
// `equipo_id`: the backend creates only the `InscripcionPersona` and claims the
// paid cup when there is free capacity.
//
// Placing a participant in a team is a different operation:
// `POST /inscripciones/{id}/pool/asignar` (`asignarPoolAEquipo()`).

// ── Edit / Delete participant ─────────────────────────────────────────────────

export interface EditarParticipantePayload {
  rol?: string;
  talla_camiseta?: string | null;
  aseguradora_nombre?: string | null;
  aseguradora_numero_poliza?: string | null;
  notas?: string | null;
}

export async function editarParticipante(
  inscripcionId: string,
  participanteId: string,
  payload: EditarParticipantePayload,
): Promise<ApiResponse<ParticipanteOut>> {
  // Backend endpoint: PATCH /participaciones/{participacion_id}
  const { data } = await api.patch<ApiResponse<ParticipanteOut>>(
    `/participaciones/${participanteId}`,
    payload,
  );
  return data;
}

export async function eliminarParticipante(
  inscripcionId: string,
  participanteId: string,
): Promise<ApiResponse<{ participante_id: string }>> {
  // Backend endpoint: PATCH /participaciones/{participacion_id}/retirar
  // (No hard delete — retiro sets estado to R)
  const { data } = await api.patch<ApiResponse<{ participante_id: string }>>(
    `/participaciones/${participanteId}/retirar`,
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
