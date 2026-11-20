import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { apiSend } from "@/lib/api";
import { apiResponseSchema } from "@/types/api.types";
import {
  type SesionUsuario,
  SesionUsuarioSchema,
} from "../schemas/sesion.schema";

/**
 * The route of the current session.
 *
 * `GET /api/auth/me` — REGISTERED: `AuthController` lives in the closed list
 * of `controllers_registrados()` (`Aplicacion/backend/config/api.py`).
 *
 * The path is written WITHOUT the `/api` prefix because the transport owner
 * (`src/lib/api.ts`) already carries the namespace of the API.
 */
export const SESION_ACTUAL_PATH = "/auth/me";

/** The envelope of this read, with the EXACT mirror of its wrapper. */
const sesionActualResponseSchema = apiResponseSchema(SesionUsuarioSchema);

/**
 * Reads the facts of the session of the authenticated actor.
 *
 * The answer is the authority of the BACKEND: the functional role, the
 * capabilities and the technical policy. The frontend draws them and never
 * decides them, and the backend evaluates them again on every request.
 *
 * A `401` is NOT a failure of the connection: it is the answer "there is no
 * session". The error travels with its status so the caller can draw the
 * expired-session state instead of a generic failure.
 */
export async function obtenerSesionActual(): Promise<SesionUsuario> {
  let estado: number;
  let cuerpo: unknown;

  try {
    const respuesta = await apiSend<unknown>("GET", SESION_ACTUAL_PATH);
    estado = respuesta.status;
    cuerpo = respuesta.data;
  } catch (error) {
    const manejado = handleApiError(error);
    throw new ApiQueryError(manejado.message, manejado.status);
  }

  // A `204` has NO body: it is never parsed (`FREEZE-ENV-1.0.0` §4.4).
  if (estado === 204) {
    throw new ApiQueryError("La sesión respondió sin contenido.", estado);
  }

  const envelope = sesionActualResponseSchema.safeParse(cuerpo);

  if (!envelope.success) {
    throw new ApiQueryError(
      "La respuesta de la sesión no cumple el contrato.",
      estado,
    );
  }

  if (!envelope.data.success) {
    throw new ApiQueryError(
      envelope.data.error?.message ?? "No se pudo leer la sesión.",
      estado,
    );
  }

  if (envelope.data.data === null) {
    throw new ApiQueryError("La sesión vino sin contenido.", estado);
  }

  return envelope.data.data;
}
