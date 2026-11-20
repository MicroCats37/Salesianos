import { getErrorMessage } from "@/errors";
import type { EstadoSuperficie } from "../types/operaciones.types";
import { ErrorAdmin } from "../services/admin.service";

/**
 * How a failure becomes a STATE of the administration area.
 *
 * The ten states of the area are declared in `SH-03` §4. This file owns the
 * mapping between the answer of the backend and the four states that a READ
 * can be in:
 *
 * | The backend | The state |
 * |---|---|
 * | the route is not registered | `sin-datos` (the honest default) |
 * | the request is in flight | `cargando` |
 * | `401` / `403` | `sin-permiso` |
 * | any other failure | `error` |
 * | a successful answer | `listo` |
 *
 * ## The rule that decides the branch
 *
 * The interface branches on the HTTP STATUS and NEVER on the machine code:
 * the catalogue of public codes is not closed, so a component that decided
 * what a code means would break with the next code the backend catalogues
 * (`contract/api-wrapper-presenter-contract.md` §8).
 *
 * The TEXT of a failure is the `message` of the backend, printed VERBATIM:
 * the frontend never translates a public message.
 */

/** The HTTP status of a failure, when the failure carries one. */
export function statusDeError(error: unknown): number | undefined {
  const fallo = error as
    | { status?: number; response?: { status?: number } }
    | undefined;

  return fallo?.status ?? fallo?.response?.status;
}

/** The public prose of a failure. */
export function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorAdmin) return error.message;

  return getErrorMessage(error);
}

/**
 * The field-level errors of a failure, as the `{ field: message }` map that
 * React Hook Form's `setError` consumes.
 *
 * Only the FROZEN channel travels (`error.field_errors[]`): the legacy
 * channels of `@/errors` belong to the endpoints that still answer in the old
 * format and the administration area answers in the frozen one.
 */
export function erroresDeCampoDeError(
  error: unknown,
): Record<string, string> {
  if (!(error instanceof ErrorAdmin)) return {};

  const errores: Record<string, string> = {};

  for (const errorDeCampo of error.erroresDeCampo) {
    errores[errorDeCampo.campo] = errorDeCampo.mensaje;
  }

  return errores;
}

/** The shape of the result of a read that this file needs. */
export interface ConsultaAdmin<T> {
  isPending: boolean;
  isError: boolean;
  data: T | undefined;
  error: unknown;
}

/**
 * The state of a surface of the administration area, from the result of its
 * read.
 *
 * `registrado` is the registration truth of the route: when the route does
 * not exist, the surface shows the HONEST state (`sin-datos`) and NEVER a
 * spinner that never ends, an invented list or an empty table.
 *
 * `project` maps the answer of the server to what the view consumes: a
 * paginated answer is projected to its items, because the browser NEVER
 * computes a page (`D-UI04-10`).
 */
export function estadoDesdeConsulta<T, R = T>(
  consulta: ConsultaAdmin<T>,
  registrado: boolean,
  project?: (datos: T) => R,
): EstadoSuperficie<R> {
  if (!registrado) {
    return { estado: "sin-datos" };
  }

  if (consulta.isError) {
    const status = statusDeError(consulta.error);

    if (status === 401 || status === 403) {
      return {
        estado: "sin-permiso",
        mensaje: mensajeDeError(consulta.error),
      };
    }

    return { estado: "error", mensaje: mensajeDeError(consulta.error) };
  }

  if (consulta.isPending || consulta.data === undefined) {
    return { estado: "cargando" };
  }

  return {
    estado: "listo",
    datos: project ? project(consulta.data) : (consulta.data as R),
  };
}
