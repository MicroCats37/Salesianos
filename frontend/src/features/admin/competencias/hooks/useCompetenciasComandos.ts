"use client";

import {
  type QueryClient,
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AvanceConfirmarFormData,
  AvanceConfirmarPayload,
  AvanceEnvelope,
  AvancePreviewEnvelope,
  CompetenciaEquipoCreateFormData,
  CompetenciaEquipoCreatePayload,
  CompetenciaEquipoEnvelope,
  CompetenciaEquipoUpdateFormData,
  CompetenciaEquipoUpdatePayload,
  CorreccionConfirmarPayload,
  CorreccionEnvelope,
  CorreccionFormData,
  CorreccionPreviewEnvelope,
  CorreccionPreviewPayload,
  EncuentroByePayload,
  EncuentroCreateFormData,
  EncuentroCreatePayload,
  EncuentroDesenlaceFormData,
  EncuentroDesenlacePayload,
  EncuentroEnlaceFormData,
  EncuentroEnlacePayload,
  EncuentroEnvelope,
  EncuentroParticipantesFormData,
  EncuentroParticipantesPayload,
  EncuentroProgramacionFormData,
  EncuentroProgramacionPayload,
  ResultadoEncuentroFormData,
  ResultadoEncuentroPayload,
  RondaCreateFormData,
  RondaCreatePayload,
  RondaEnvelope,
  RondaUpdateFormData,
  RondaUpdatePayload,
} from "../schemas";
import {
  actualizarEquipoCompetencia,
  actualizarParticipantesEncuentro,
  actualizarRondaCompetencia,
  configurarByeEncuentro,
  confirmarAvance,
  confirmarCorreccion,
  crearEncuentroCompetencia,
  crearEquipoCompetencia,
  crearRondaCompetencia,
  desenlazarEncuentro,
  enlazarEncuentro,
  previsualizarAvance,
  previsualizarCorreccion,
  programarEncuentro,
  registrarResultadoEncuentro,
} from "../services";
import {
  CLAVES_COMPETENCIA_AGENDA,
  CLAVES_COMPETENCIA_LISTA,
  claveCompetenciaCuadro,
  claveCompetenciaDetalle,
} from "../utils/competencias.claves.utils";

/**
 * The mutations of the module — TanStack Query owns EVERY piece of server
 * state, including the writes.
 *
 * Two decisions of this module:
 *
 * 1. The PAYLOAD is built HERE, never in the form component: the form only
 *    collects what the administrator typed (`contract/next-app-architecture-contract.md`
 *    §5). The optimistic lock (`expected_version`) is added here too: it is
 *    the version the SERVER returned, never a value the administrator types.
 * 2. Every write invalidates the EXACT keys of the reads of the module: the
 *    detail and the bracket of the competition (by identifier) and the list
 *    and the agenda (whose filters are part of their key).
 */

// ── Variables de cada comando ────────────────────────────────────────────────

/** Variables of the registration of a team (the MANUAL seed of the bracket). */
export interface VariablesEquipoAlta {
  competenciaId: string;
  datos: CompetenciaEquipoCreateFormData;
}

/** Variables of the edition of a participation. */
export interface VariablesEquipoEdicion {
  competenciaId: string;
  equipoId: string;
  expectedVersion: number;
  datos: CompetenciaEquipoUpdateFormData;
}

/** Variables of the creation of a round. */
export interface VariablesRondaAlta {
  competenciaId: string;
  datos: RondaCreateFormData;
}

/** Variables of the edition of a round. */
export interface VariablesRondaEdicion {
  competenciaId: string;
  rondaId: string;
  expectedVersion: number;
  datos: RondaUpdateFormData;
}

/** Variables of the creation of an encounter. */
export interface VariablesEncuentroAlta {
  competenciaId: string;
  datos: EncuentroCreateFormData;
}

/** Variables of the edition of the participants of an encounter. */
export interface VariablesParticipantes {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: EncuentroParticipantesFormData;
}

/** Variables of the schedule of an encounter. */
export interface VariablesProgramacion {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: EncuentroProgramacionFormData;
}

/** Variables of the MANUAL bye of an encounter. */
export interface VariablesBye {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: EncuentroDesenlaceFormData;
}

/** Variables of the link of an encounter to the next one. */
export interface VariablesEnlace {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: EncuentroEnlaceFormData;
}

/** Variables of the removal of the link of an encounter. */
export interface VariablesDesenlace {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: EncuentroDesenlaceFormData;
}

/** Variables of the registration of the result of an encounter. */
export interface VariablesResultado {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: ResultadoEncuentroFormData;
}

/** Variables of the confirmation of the propagation of the winner. */
export interface VariablesAvance {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: AvanceConfirmarFormData;
}

/** Variables of the confirmation of the correction of the winner. */
export interface VariablesCorreccion {
  competenciaId: string;
  encuentroId: string;
  expectedVersion: number;
  datos: CorreccionFormData;
}

// ── Construcción de los payloads ─────────────────────────────────────────────

/** Payload of the registration of a team. */
export function construirPayloadEquipoAlta(
  datos: CompetenciaEquipoCreateFormData,
): CompetenciaEquipoCreatePayload {
  return { equipo_id: datos.equipo_id, orden: datos.orden };
}

/** Payload of the edition of a participation. */
export function construirPayloadEquipoEdicion(
  variables: VariablesEquipoEdicion,
): CompetenciaEquipoUpdatePayload {
  return {
    orden: variables.datos.orden,
    estado: variables.datos.estado,
    motivo: variables.datos.motivo,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the creation of a round. */
export function construirPayloadRondaAlta(
  datos: RondaCreateFormData,
): RondaCreatePayload {
  return { etiqueta: datos.etiqueta, orden: datos.orden };
}

/** Payload of the edition of a round. */
export function construirPayloadRondaEdicion(
  variables: VariablesRondaEdicion,
): RondaUpdatePayload {
  return {
    etiqueta: variables.datos.etiqueta,
    orden: variables.datos.orden,
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the creation of an encounter. */
export function construirPayloadEncuentroAlta(
  datos: EncuentroCreateFormData,
): EncuentroCreatePayload {
  return {
    ronda_id: datos.ronda_id,
    orden: datos.orden,
    participante_1_id: datos.participante_1_id ?? null,
    participante_2_id: datos.participante_2_id ?? null,
  };
}

/** Payload of the edition of the participants of an encounter. */
export function construirPayloadParticipantes(
  variables: VariablesParticipantes,
): EncuentroParticipantesPayload {
  return {
    participante_1_id: variables.datos.participante_1_id ?? null,
    participante_2_id: variables.datos.participante_2_id ?? null,
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/**
 * Payload of the schedule of an encounter.
 *
 * The two instants are composed from the day and the two times of the form:
 * the schedule of an encounter ALWAYS shares the date of its competition.
 */
export function construirPayloadProgramacion(
  variables: VariablesProgramacion,
): EncuentroProgramacionPayload {
  return {
    inicio_programado: `${variables.datos.fecha}T${variables.datos.hora_inicio}:00`,
    fin_programado: `${variables.datos.fecha}T${variables.datos.hora_fin}:00`,
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the MANUAL bye of an encounter. */
export function construirPayloadBye(
  variables: VariablesBye,
): EncuentroByePayload {
  return {
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the link of an encounter to the next one. */
export function construirPayloadEnlace(
  variables: VariablesEnlace,
): EncuentroEnlacePayload {
  return {
    siguiente_encuentro_id: variables.datos.siguiente_encuentro_id,
    slot_destino: variables.datos.slot_destino,
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the removal of the link of an encounter. */
export function construirPayloadDesenlace(
  variables: VariablesDesenlace,
): EncuentroDesenlacePayload {
  return {
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the registration of the result of an encounter. */
export function construirPayloadResultado(
  variables: VariablesResultado,
): ResultadoEncuentroPayload {
  return {
    ganador_id: variables.datos.ganador_id,
    puntaje_1: variables.datos.puntaje_1 ?? null,
    puntaje_2: variables.datos.puntaje_2 ?? null,
    marcador_detalle: variables.datos.marcador_detalle || null,
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/** Payload of the confirmation of the propagation of the winner. */
export function construirPayloadAvance(
  variables: VariablesAvance,
): AvanceConfirmarPayload {
  return {
    motivo: variables.datos.motivo ?? null,
    expected_version: variables.expectedVersion,
  };
}

/**
 * Payload of the confirmation of the correction of the winner.
 *
 * `override` and `acepta_impacto` travel ONLY when the administrator
 * accepted the impact that the preview exposed: without that acceptance the
 * correction changes NOTHING (never a silent cascade).
 */
export function construirPayloadCorreccion(
  variables: VariablesCorreccion,
): CorreccionConfirmarPayload {
  const aceptaImpacto = variables.datos.acepta_impacto === true;
  return {
    ganador_id: variables.datos.ganador_id,
    motivo: variables.datos.motivo,
    override: aceptaImpacto,
    acepta_impacto: aceptaImpacto,
    expected_version: variables.expectedVersion,
  };
}

// ── Invalidación de las lecturas ─────────────────────────────────────────────

/**
 * Invalidate the reads of ONE competition.
 *
 * The detail and the bracket are invalidated with their EXACT key (the
 * identifier is part of it). The list and the agenda carry their filters in
 * their key, so they are invalidated by their prefix: every variant of both
 * is refreshed.
 */
export async function invalidarLecturasCompetencia(
  queryClient: QueryClient,
  competenciaId: string,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: claveCompetenciaDetalle(competenciaId),
      exact: true,
    }),
    queryClient.invalidateQueries({
      queryKey: claveCompetenciaCuadro(competenciaId),
      exact: true,
    }),
    queryClient.invalidateQueries({
      queryKey: CLAVES_COMPETENCIA_LISTA,
      exact: false,
    }),
    queryClient.invalidateQueries({
      queryKey: CLAVES_COMPETENCIA_AGENDA,
      exact: false,
    }),
  ]);
}

// ── Mutaciones ───────────────────────────────────────────────────────────────

/** Register a team in the bracket with its MANUAL order. */
export function useCrearEquipoCompetencia() {
  const queryClient = useQueryClient();
  return useMutation<
    CompetenciaEquipoEnvelope,
    ApiQueryError,
    VariablesEquipoAlta
  >({
    mutationFn: async (variables: VariablesEquipoAlta) =>
      crearEquipoCompetencia(
        variables.competenciaId,
        construirPayloadEquipoAlta(variables.datos),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Update the manual order or the state of a participation. */
export function useActualizarEquipoCompetencia() {
  const queryClient = useQueryClient();
  return useMutation<
    CompetenciaEquipoEnvelope,
    ApiQueryError,
    VariablesEquipoEdicion
  >({
    mutationFn: async (variables: VariablesEquipoEdicion) =>
      actualizarEquipoCompetencia(
        variables.competenciaId,
        variables.equipoId,
        construirPayloadEquipoEdicion(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Create a round of the bracket. */
export function useCrearRondaCompetencia() {
  const queryClient = useQueryClient();
  return useMutation<RondaEnvelope, ApiQueryError, VariablesRondaAlta>({
    mutationFn: async (variables: VariablesRondaAlta) =>
      crearRondaCompetencia(
        variables.competenciaId,
        construirPayloadRondaAlta(variables.datos),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Update the label or the order of a round. */
export function useActualizarRondaCompetencia() {
  const queryClient = useQueryClient();
  return useMutation<RondaEnvelope, ApiQueryError, VariablesRondaEdicion>({
    mutationFn: async (variables: VariablesRondaEdicion) =>
      actualizarRondaCompetencia(
        variables.competenciaId,
        variables.rondaId,
        construirPayloadRondaEdicion(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Create an encounter in a round of the bracket. */
export function useCrearEncuentroCompetencia() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesEncuentroAlta>({
    mutationFn: async (variables: VariablesEncuentroAlta) =>
      crearEncuentroCompetencia(
        variables.competenciaId,
        construirPayloadEncuentroAlta(variables.datos),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Move the teams of the two slots of an encounter. */
export function useActualizarParticipantesEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesParticipantes>({
    mutationFn: async (variables: VariablesParticipantes) =>
      actualizarParticipantesEncuentro(
        variables.encuentroId,
        construirPayloadParticipantes(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Schedule an encounter. */
export function useProgramarEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesProgramacion>({
    mutationFn: async (variables: VariablesProgramacion) =>
      programarEncuentro(
        variables.encuentroId,
        construirPayloadProgramacion(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Configure a MANUAL bye. */
export function useConfigurarByeEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesBye>({
    mutationFn: async (variables: VariablesBye) =>
      configurarByeEncuentro(
        variables.encuentroId,
        construirPayloadBye(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Link an encounter to the next encounter of the bracket. */
export function useEnlazarEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesEnlace>({
    mutationFn: async (variables: VariablesEnlace) =>
      enlazarEncuentro(
        variables.encuentroId,
        construirPayloadEnlace(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Remove the link of an encounter. */
export function useDesenlazarEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesDesenlace>({
    mutationFn: async (variables: VariablesDesenlace) =>
      desenlazarEncuentro(
        variables.encuentroId,
        construirPayloadDesenlace(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Register the AUTHORITATIVE result of an encounter. */
export function useRegistrarResultadoEncuentro() {
  const queryClient = useQueryClient();
  return useMutation<EncuentroEnvelope, ApiQueryError, VariablesResultado>({
    mutationFn: async (variables: VariablesResultado) =>
      registrarResultadoEncuentro(
        variables.encuentroId,
        construirPayloadResultado(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Place the winner in the linked slot of the next encounter. */
export function useConfirmarAvance() {
  const queryClient = useQueryClient();
  return useMutation<AvanceEnvelope, ApiQueryError, VariablesAvance>({
    mutationFn: async (variables: VariablesAvance) =>
      confirmarAvance(variables.encuentroId, construirPayloadAvance(variables)),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

/** Correct the authoritative winner of an encounter. */
export function useConfirmarCorreccion() {
  const queryClient = useQueryClient();
  return useMutation<CorreccionEnvelope, ApiQueryError, VariablesCorreccion>({
    mutationFn: async (variables: VariablesCorreccion) =>
      confirmarCorreccion(
        variables.encuentroId,
        construirPayloadCorreccion(variables),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasCompetencia(queryClient, variables.competenciaId);
    },
  });
}

// ── Previsualizaciones (nunca escriben) ──────────────────────────────────────

/**
 * The proposal of the propagation of the winner.
 *
 * The preview NEVER writes: it is the proposal that the administrator
 * confirms. It is NOT retried automatically: a failure must be visible and
 * retryable by hand.
 */
export const previsualizacionAvanceQueryOptions = (
  encuentroId: string,
  habilitado = true,
) =>
  queryOptions<
    AvancePreviewEnvelope,
    ApiQueryError,
    AvancePreviewEnvelope,
    readonly ["admin", "competencias", "avance", "preview", string]
  >({
    queryKey: ["admin", "competencias", "avance", "preview", encuentroId],
    queryFn: () => previsualizarAvance(encuentroId),
    enabled: habilitado && encuentroId.length > 0,
    retry: false,
    staleTime: 0,
  });

/** The impact analysis of the correction of the winner. */
export const previsualizacionCorreccionQueryOptions = (
  encuentroId: string,
  ganadorId: string,
  habilitado = true,
) =>
  queryOptions<
    CorreccionPreviewEnvelope,
    ApiQueryError,
    CorreccionPreviewEnvelope,
    readonly ["admin", "competencias", "correccion", "preview", string, string]
  >({
    queryKey: [
      "admin",
      "competencias",
      "correccion",
      "preview",
      encuentroId,
      ganadorId,
    ],
    queryFn: () =>
      previsualizarCorreccion(
        encuentroId,
        construirPayloadCorreccionPreview(ganadorId),
      ),
    enabled: habilitado && encuentroId.length > 0 && ganadorId.length > 0,
    retry: false,
    staleTime: 0,
  });

/** Payload of the preview of the correction: only the proposed winner. */
export function construirPayloadCorreccionPreview(
  ganadorId: string,
): CorreccionPreviewPayload {
  return { ganador_id: ganadorId };
}

/** The proposal of the propagation of the winner. */
export function usePrevisualizarAvance(encuentroId: string, habilitado = true) {
  return useQuery(previsualizacionAvanceQueryOptions(encuentroId, habilitado));
}

/** The impact analysis of the correction of the winner. */
export function usePrevisualizarCorreccion(
  encuentroId: string,
  ganadorId: string,
  habilitado = true,
) {
  return useQuery(
    previsualizacionCorreccionQueryOptions(encuentroId, ganadorId, habilitado),
  );
}
