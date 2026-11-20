import { apiSend } from "@/lib/api";
import type {
  CompetenciaCrear,
  EquipoEditar,
  EquipoIncorporar,
} from "../schemas/competencia.schema";
import {
  competenciaCrearSchema,
  competenciaDetalleEnvelope,
  competenciaEquipoEnvelope,
  competenciasListaEnvelope,
  cuadroEnvelope,
  equipoEditarSchema,
  equipoIncorporarSchema,
  equiposElegiblesEnvelope,
} from "../schemas/competencia.schema";
import type {
  CompetenciaDetalle,
  CompetenciaEquipo,
  CompetenciaListado,
  ConsultaCompetenciasParams,
  EquipoElegible,
  Ronda,
} from "../types/competencia.types";

/**
 * The client of the COMPETITIONS area.
 *
 * | Route | Method | Presenter | Wrapper |
 * |---|---|---|---|
 * | `GET /competencias` | GET | `CompetenciasPresenter.present_listado` | `list[CompetenciaListadoOut]` |
 *
 * Backend: `CompetenciasController` (packet `DOM-07`), REGISTERED in
 * `Aplicacion/backend/config/api.py`. The route requires a session
 * (`JWTAuth`) and the permission of reading the area (`RequireAdminVer`).
 *
 * ## The shape of the answer
 *
 * The route publishes a RAW LIST inside the standard envelope of the target
 * (`FREEZE-ENV-1.0.0`): there is NO pagination block, because the route
 * publishes the whole list of the edition. The mirror of that answer is
 * `competenciasListaEnvelope`
 * (`schemas/competencia.schema.ts`).
 *
 * ## The filters
 *
 * The route accepts `disciplina_id`, `categoria_id` and `estado`, and NOTHING
 * else: the edition is resolved by the server (`FR-02` §2.2) and the route
 * does not paginate. A filter that is absent is NOT sent, so the request
 * without filters and the request with an empty filter are the SAME request.
 *
 * ## What the browser NEVER does
 *
 * It never derives the competitive band of a team and it never counts the
 * teams or the encounters of a bracket: the three counters are published by
 * the presenter (`RN-A02`).
 */
export const RUTA_COMPETENCIAS = "/competencias";

/**
 * The routes of the area, with their parameters.
 *
 * They are EXPOSED here and nowhere else: the generic hooks (`useApiQuery`,
 * `useApiCreate`, …) build the URL of the endpoint they call, and a component
 * never spells a path.
 */
export const rutasCompetencias = {
  /** The list of the edition (`GET /competencias`). */
  lista: RUTA_COMPETENCIAS,
  /** The detail of ONE competition (`GET /competencias/{id}`). */
  detalle: (competenciaId: string) => `${RUTA_COMPETENCIAS}/${competenciaId}`,
  /** The bracket of ONE competition (`GET /competencias/{id}/cuadro`). */
  cuadro: (competenciaId: string) =>
    `${RUTA_COMPETENCIAS}/${competenciaId}/cuadro`,
  /** The eligible teams of ONE competition. */
  equiposElegibles: (competenciaId: string) =>
    `${RUTA_COMPETENCIAS}/${competenciaId}/equipos-elegibles`,
  /** The incorporation of a team into the bracket (`POST …/equipos`). */
  incorporarEquipo: (competenciaId: string) =>
    `${RUTA_COMPETENCIAS}/${competenciaId}/equipos`,
  /** The edition of a team of the bracket (`PATCH …/equipos/{equipo_id}`). */
  editarEquipo: (competenciaId: string, equipoId: string) =>
    `${RUTA_COMPETENCIAS}/${competenciaId}/equipos/${equipoId}`,
  /** The generation of the bracket (`POST …/cuadro/generar`). */
  generarCuadro: (competenciaId: string) =>
    `${RUTA_COMPETENCIAS}/${competenciaId}/cuadro/generar`,
} as const;

/**
 * The parameters that travel in the query string.
 *
 * A filter that is absent does NOT travel: an absent filter and a filter
 * with an empty value are the SAME request.
 */
export function parametrosDeConsulta(
  params: ConsultaCompetenciasParams,
): Record<string, string> {
  const consulta: Record<string, string> = {};

  if (params.disciplina_id) consulta.disciplina_id = params.disciplina_id;
  if (params.categoria_id) consulta.categoria_id = params.categoria_id;
  if (params.estado) consulta.estado = params.estado;

  return consulta;
}

/**
 * The competitions of the edition, with their three counters.
 *
 * @param params the filters of the route. An absent filter is not sent.
 */
export async function obtenerCompetencias(
  params: ConsultaCompetenciasParams = {},
): Promise<CompetenciaListado[]> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_COMPETENCIAS,
    undefined,
    { params: parametrosDeConsulta(params) },
  );

  if (status === 204) {
    throw new Error("La lista de competencias respondió sin contenido.");
  }

  const envelope = competenciasListaEnvelope.parse(data);

  if (!envelope.success || envelope.data === null) {
    throw new Error(
      envelope.message ?? "El servidor no devolvió la lista de competencias.",
    );
  }

  return envelope.data;
}

/** Creates a competition in the edition resolved by the server. */
export async function crearCompetencia(
  payload: CompetenciaCrear,
): Promise<CompetenciaDetalle> {
  const cuerpo = competenciaCrearSchema.parse(payload);
  const { status, data } = await apiSend<unknown>(
    "post",
    RUTA_COMPETENCIAS,
    cuerpo,
  );

  if (status !== 201) {
    throw new Error("No se pudo registrar la competencia.");
  }

  const envelope = competenciaDetalleEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo registrar la competencia.");
  }

  return envelope.data;
}

export async function obtenerCompetencia(
  competenciaId: string,
): Promise<CompetenciaDetalle> {
  const { data } = await apiSend<unknown>(
    "get",
    rutasCompetencias.detalle(competenciaId),
  );
  const envelope = competenciaDetalleEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo obtener la competencia.");
  }
  return envelope.data;
}

export async function obtenerCuadro(competenciaId: string): Promise<Ronda[]> {
  const { data } = await apiSend<unknown>(
    "get",
    rutasCompetencias.cuadro(competenciaId),
  );
  const envelope = cuadroEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo obtener el cuadro.");
  }
  return envelope.data;
}

export async function obtenerEquiposElegibles(
  competenciaId: string,
): Promise<EquipoElegible[]> {
  const { data } = await apiSend<unknown>(
    "get",
    rutasCompetencias.equiposElegibles(competenciaId),
  );
  const envelope = equiposElegiblesEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(
      envelope.message ?? "No se pudieron consultar los equipos elegibles.",
    );
  }
  return envelope.data;
}

export async function incorporarEquipo(
  competenciaId: string,
  payload: EquipoIncorporar,
): Promise<CompetenciaEquipo> {
  const { data } = await apiSend<unknown>(
    "post",
    rutasCompetencias.incorporarEquipo(competenciaId),
    equipoIncorporarSchema.parse(payload),
  );
  const envelope = competenciaEquipoEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo incorporar el equipo.");
  }
  return envelope.data;
}

export async function editarEquipo(
  competenciaId: string,
  equipoId: string,
  payload: EquipoEditar,
): Promise<CompetenciaEquipo> {
  const { data } = await apiSend<unknown>(
    "patch",
    rutasCompetencias.editarEquipo(competenciaId, equipoId),
    equipoEditarSchema.parse(payload),
  );
  const envelope = competenciaEquipoEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo actualizar el equipo.");
  }
  return envelope.data;
}

export async function generarCuadro(
  competenciaId: string,
): Promise<CompetenciaDetalle> {
  const { status, data } = await apiSend<unknown>(
    "post",
    rutasCompetencias.generarCuadro(competenciaId),
  );
  if (status !== 201) throw new Error("No se pudo generar el cuadro.");
  const envelope = competenciaDetalleEnvelope.parse(data);
  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudo generar el cuadro.");
  }
  return envelope.data;
}
