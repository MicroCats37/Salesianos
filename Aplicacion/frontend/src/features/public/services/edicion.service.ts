import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { apiSend } from "@/lib/api";
import { apiResponseSchema } from "@/types/api.types";
import {
  type EdicionActual,
  EdicionActualSchema,
} from "../schemas/edicion.schema";

/**
 * The route of the current edition.
 *
 * `RT-ED-01` — `GET /api/ediciones/actual`.
 * It is REGISTERED: `EdicionController` lives in the closed list of
 * `controllers_registrados()` (`Aplicacion/backend/config/api.py`) and the
 * route is in `RUTAS_DE_DOMINIO_CONGELADAS`.
 *
 * The path is written WITHOUT the `/api` prefix because the transport owner
 * (`src/lib/api.ts`) already carries the namespace of the API.
 */
export const EDICION_ACTUAL_PATH = "/ediciones/actual";

/**
 * The envelope of this read.
 *
 * It is the shared envelope factory (`apiResponseSchema`) with the EXACT
 * mirror of the wrapper of this dataset. The error branch of the envelope is
 * read by the shared error handler (`handleApiError`); the success branch is
 * parsed here, loudly.
 */
export const edicionActualResponseSchema =
  apiResponseSchema(EdicionActualSchema);

/**
 * Reads the edition that the backend publishes as the current one.
 *
 * The read NEVER invents an edition: when the backend answers `404`
 * (`EDICION_NO_PUBLICADA`) or `409` (`EDICION_AMBIGUA`) the error travels
 * with its status, and the caller decides which state to draw. The frontend
 * does not resolve the edition by itself and it does not fall back to a
 * previous edition.
 */
export async function obtenerEdicionActual(): Promise<EdicionActual> {
  let estado: number;
  let cuerpo: unknown;

  try {
    const respuesta = await apiSend<unknown>("GET", EDICION_ACTUAL_PATH);
    estado = respuesta.status;
    cuerpo = respuesta.data;
  } catch (error) {
    const manejado = handleApiError(error);
    throw new ApiQueryError(manejado.message, manejado.status);
  }

  // A `204` has NO body: it is never parsed (`FREEZE-ENV-1.0.0` §4.4).
  if (estado === 204) {
    throw new ApiQueryError(
      "La edición vigente respondió sin contenido.",
      estado,
    );
  }

  const envelope = edicionActualResponseSchema.safeParse(cuerpo);

  if (!envelope.success) {
    throw new ApiQueryError(
      "La respuesta de la edición vigente no cumple el contrato.",
      estado,
    );
  }

  if (!envelope.data.success) {
    throw new ApiQueryError(
      envelope.data.error?.message ?? "No se pudo leer la edición vigente.",
      estado,
    );
  }

  if (envelope.data.data === null) {
    throw new ApiQueryError("La edición vigente vino sin contenido.", estado);
  }

  return envelope.data.data;
}
