"use client";

import type { QueryKey } from "@tanstack/react-query";
import {
  apiQueryOptions,
  useApiCreate,
  useApiQuery,
  useApiUpdate,
} from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { claveEncuentrosPublicos } from "../publico/utils/encuentro-publico.claves.utils";
import type {
  AvanceConfirmar,
  CompetenciaCrear,
  CorreccionAplicar,
  CorreccionPrevisualizar,
  EncuentroActualizar,
  EquipoEditar,
  EquipoIncorporar,
  ResultadoRegistrar,
} from "../schemas/competencia.schema";
import {
  avanceEnvelope,
  avancePreviewEnvelope,
  competenciaDetalleEnvelope,
  competenciaEquipoEnvelope,
  competenciasListaEnvelope,
  correccionEnvelope,
  correccionPreviewEnvelope,
  cuadroEnvelope,
  encuentroEnvelope,
  equiposElegiblesEnvelope,
  resultadoRegistradoEnvelope,
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

// ── El ciclo de vida del encuentro ─────────────────────────────────────────
//
// Un cambio de un encuentro NO es un cambio de la competencia: el panel del
// encuentro es su único editor (`GOV-02-RB-05a`) y estas son sus mutaciones.
//
// Las dos VISTAS PREVIAS (`avance/preview` y `correccion/preview`) NO
// ESCRIBEN NADA: simulan el efecto y lo publican. Por eso NO invalidan
// ninguna clave: una simulación no puede ensuciar la caché.

/**
 * The reads that a change of an encounter dirties.
 *
 * The ADMINISTRATION of the competition AND the PUBLIC surface of the
 * encounters show the same fact: if the operator starts a match, the public
 * page must stop saying that it is programmed. Both keys are declared
 * EXPLICITLY (`clavesCompetencias.all` covers the reads of the area and
 * `claveEncuentrosPublicos` the public read).
 */
const CLAVES_DIRTAS_POR_UN_ENCUENTRO: readonly QueryKey[] = [
  clavesCompetencias.all,
  claveEncuentrosPublicos,
];

/**
 * The update of ONE encounter (`PATCH …/encuentros/{encuentro_id}`).
 *
 * The route carries TWO identifiers and the payload carries NONE of them: the
 * competition travels in `id` and the encounter in `params`, and the body is
 * only the command (`GOV-02-RB-05a`).
 *
 * The payload ALWAYS carries `expected_version`: the browser never decides
 * whether a write is current (`RB-05` ADM-11).
 */
export function useActualizarEncuentro() {
  const mutacion = useApiUpdate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.encuentro(String(id), params?.encuentro_id ?? ""),
    method: "PATCH",
    schema: datosDelEnvelope(encuentroEnvelope),
    invalidateKeys: CLAVES_DIRTAS_POR_UN_ENCUENTRO,
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      encuentroId: string;
      datos: EncuentroActualizar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

/**
 * The registration of the authoritative result (`POST …/resultado`).
 *
 * The winner travels in the payload and it is DECLARED by the operator: the
 * score never decides it (`GOV-02-RB-05c`).
 */
export function useRegistrarResultado() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.resultado(String(id), params?.encuentro_id ?? ""),
    schema: datosDelEnvelope(resultadoRegistradoEnvelope),
    invalidateKeys: CLAVES_DIRTAS_POR_UN_ENCUENTRO,
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      encuentroId: string;
      datos: ResultadoRegistrar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

/**
 * The preview of the advance (`POST …/avance/preview`).
 *
 * It NEVER writes, so it dirties NOTHING: the cache is untouched because
 * nothing changed (`QA-K04`).
 */
export function usePrevisualizarAvance() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.avancePreview(String(id), params?.encuentro_id ?? ""),
    schema: datosDelEnvelope(avancePreviewEnvelope),
    invalidateKeys: [],
    showSuccessToast: false,
  });

  return {
    ...mutacion,
    mutateAsync: (args: { competenciaId: string; encuentroId: string }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: undefined,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

/** The confirmation of the advance (`POST …/avance`). */
export function useConfirmarAvance() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.avance(String(id), params?.encuentro_id ?? ""),
    schema: datosDelEnvelope(avanceEnvelope),
    invalidateKeys: CLAVES_DIRTAS_POR_UN_ENCUENTRO,
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      encuentroId: string;
      datos: AvanceConfirmar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

/**
 * The preview of a correction (`POST …/correccion/preview`).
 *
 * It NEVER writes and it dirties NOTHING (`QA-K03`).
 */
export function usePrevisualizarCorreccion() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.correccionPreview(
        String(id),
        params?.encuentro_id ?? "",
      ),
    schema: datosDelEnvelope(correccionPreviewEnvelope),
    invalidateKeys: [],
    showSuccessToast: false,
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      encuentroId: string;
      datos: CorreccionPrevisualizar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

/**
 * The application of a correction (`POST …/correccion`).
 *
 * The reason is MANDATORY and the cascade needs BOTH `override` AND
 * `acepta_impacto`: the browser never decides that the impact is accepted.
 */
export function useCorregirEncuentro() {
  const mutacion = useApiCreate({
    getUrl: ({ id, params }) =>
      rutasCompetencias.correccion(String(id), params?.encuentro_id ?? ""),
    schema: datosDelEnvelope(correccionEnvelope),
    invalidateKeys: CLAVES_DIRTAS_POR_UN_ENCUENTRO,
  });

  return {
    ...mutacion,
    mutateAsync: (args: {
      competenciaId: string;
      encuentroId: string;
      datos: CorreccionAplicar;
    }) =>
      mutacion.mutateAsync({
        id: args.competenciaId,
        data: args.datos,
        params: { encuentro_id: args.encuentroId },
      }),
  };
}

export type { CompetenciaCrear, EquipoEditar };
