"use client";

import { apiQueryOptions, useApiCreate, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type {
  CompetenciaCrear,
  EquipoEditar,
  EquipoIncorporar,
} from "../schemas/competencia.schema";
import {
  competenciaDetalleEnvelope,
  competenciaEquipoEnvelope,
  competenciasListaEnvelope,
  cuadroEnvelope,
  equiposElegiblesEnvelope,
} from "../schemas/competencia.schema";
import {
  RUTA_COMPETENCIAS,
  rutasCompetencias,
} from "../services/competencia.service";
import type { ConsultaCompetenciasParams } from "../types/competencia.types";
import {
  claveCompetenciaCuadro,
  claveCompetenciaDetalle,
  claveEquiposElegibles,
  clavesCompetencias,
} from "../utils/competencias.claves.utils";

/**
 * The read of the list of competitions (`ADM-10`).
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the list | `GET /competencias` | `list[CompetenciaListadoOut]` |
 *
 * ## The filters travel in the key
 *
 * The filters of the URL (`estado`, `categoria_id`) change the answer, so
 * they travel in the key AND in the request: one cache entry per filter, and
 * never a second entry for the same answer
 * (`utils/competencias.claves.utils.ts`).
 *
 * ## The staleness
 *
 * The list of the competitions is an ADMINISTRATIVE list: it changes when a
 * competition is created, programmed or finished, and not by the minute. Its
 * staleness is the one of the data contract for administrative lists (thirty
 * seconds).
 */
export function useCompetenciasLista(params: ConsultaCompetenciasParams = {}) {
  return useApiQuery({
    queryKey: clavesCompetencias.list,
    url: RUTA_COMPETENCIAS,
    schema: datosDelEnvelope(competenciasListaEnvelope),
    params: {
      disciplina_id: params.disciplina_id,
      categoria_id: params.categoria_id,
      estado: params.estado,
    },
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

export function useCrearCompetencia() {
  return useApiCreate({
    url: RUTA_COMPETENCIAS,
    schema: datosDelEnvelope(competenciaDetalleEnvelope),
    invalidateKeys: [clavesCompetencias.all],
  });
}

/**
 * The `queryOptions` of ONE competition.
 *
 * It is EXPORTED so a prefetch, a server-side hydration and the component
 * read share ONE cache entry.
 */
export const competenciaDetalleQueryOptions = (competenciaId: string) =>
  apiQueryOptions({
    queryKey: claveCompetenciaDetalle(competenciaId),
    url: rutasCompetencias.detalle(competenciaId),
    schema: datosDelEnvelope(competenciaDetalleEnvelope),
    kind: "listadoAdministrativo",
  });

/** The `queryOptions` of the bracket of ONE competition. */
export const competenciaCuadroQueryOptions = (competenciaId: string) =>
  apiQueryOptions({
    queryKey: claveCompetenciaCuadro(competenciaId),
    url: rutasCompetencias.cuadro(competenciaId),
    schema: datosDelEnvelope(cuadroEnvelope),
    kind: "listadoAdministrativo",
  });

export function useCompetenciaDetalle(competenciaId: string) {
  return useApiQuery({
    queryKey: claveCompetenciaDetalle(competenciaId),
    url: competenciaId ? rutasCompetencias.detalle(competenciaId) : null,
    schema: datosDelEnvelope(competenciaDetalleEnvelope),
    queryOptions: {
      enabled: competenciaId.length > 0,
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

export function useCompetenciaCuadro(competenciaId: string) {
  return useApiQuery({
    queryKey: claveCompetenciaCuadro(competenciaId),
    url: competenciaId ? rutasCompetencias.cuadro(competenciaId) : null,
    schema: datosDelEnvelope(cuadroEnvelope),
    queryOptions: {
      enabled: competenciaId.length > 0,
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

export function useEquiposElegibles(competenciaId: string) {
  return useApiQuery({
    queryKey: claveEquiposElegibles(competenciaId),
    url: competenciaId
      ? rutasCompetencias.equiposElegibles(competenciaId)
      : null,
    schema: datosDelEnvelope(equiposElegiblesEnvelope),
    queryOptions: {
      enabled: competenciaId.length > 0,
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

/**
 * The incorporation of a team into the bracket (`RT-CP-03`).
 *
 * The identifier of the competition travels in the URL and NEVER in the
 * payload: the command is scoped to its record.
 */
export function useIncorporarEquipo() {
  const mutacion = useApiCreate({
    getUrl: ({ id }) => rutasCompetencias.incorporarEquipo(String(id)),
    schema: datosDelEnvelope(competenciaEquipoEnvelope),
    invalidateKeys: [clavesCompetencias.all],
  });

  return {
    ...mutacion,
    mutateAsync: (args: { competenciaId: string; datos: EquipoIncorporar }) =>
      mutacion.mutateAsync({ id: args.competenciaId, data: args.datos }),
  };
}

/**
 * The edition of a team of the bracket (`RT-CP-04`).
 *
 * The route carries TWO identifiers (the competition and the team) and the
 * payload carries NONE of them: the second identifier travels in the `params`
 * of the scoped mode, never in the body.
 */
export function useEditarEquipo() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.editarEquipo(String(id), params?.equipo_id ?? ""),
    schema: datosDelEnvelope(competenciaEquipoEnvelope),
    invalidateKeys: [clavesCompetencias.all],
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      equipoId: string;
      datos: EquipoEditar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { equipo_id: args.equipoId },
      }),
  };
}

/** The generation of the bracket of ONE competition (`RT-CP-05`). */
export function useGenerarCuadro() {
  const mutacion = useApiCreate({
    getUrl: ({ id }) => rutasCompetencias.generarCuadro(String(id)),
    schema: datosDelEnvelope(competenciaDetalleEnvelope),
    invalidateKeys: [clavesCompetencias.all],
  });

  return {
    ...mutacion,
    mutateAsync: (competenciaId: string) =>
      mutacion.mutateAsync({ id: competenciaId, data: undefined }),
  };
}

export type { CompetenciaCrear, EquipoEditar };
