import type {
  CompetenciaListado,
  EstadoVistaCompetencias,
} from "../types/competencia.types";
import { statusDeError } from "./competencias.errores.utils";

/**
 * How the answer of the server becomes a STATE of the competitions area.
 *
 * | The backend | The state |
 * |---|---|
 * | the request is in flight | `cargando` |
 * | `401` / `403` | `sin-permiso` |
 * | any other failure | `error` |
 * | a successful answer | `listo` |
 *
 * The rule that decides the branch is the HTTP STATUS and NEVER the machine
 * code: the catalogue of public codes is not closed
 * (`contract/api-wrapper-presenter-contract.md` §8).
 */

/** The shape of the result of a read that this file needs. */
export interface ConsultaCompetencias {
  isPending: boolean;
  isError: boolean;
  data: CompetenciaListado[] | undefined;
  error: unknown;
}

/**
 * The state of the list of competitions, from the result of its read.
 *
 * There is NO `sin-datos`: the route IS registered, so the honest states are
 * the four of the table above.
 */
export function estadoDesdeConsulta(
  consulta: ConsultaCompetencias,
): EstadoVistaCompetencias {
  if (consulta.isError) {
    const status = statusDeError(consulta.error);

    if (status === 401 || status === 403) {
      return "sin-permiso";
    }

    return "error";
  }

  if (consulta.isPending || consulta.data === undefined) {
    return "cargando";
  }

  return "listo";
}
