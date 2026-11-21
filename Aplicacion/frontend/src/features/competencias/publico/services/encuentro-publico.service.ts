import { apiSend } from "@/lib/api";
import type { TorneoPublico } from "../schemas/torneo-publico.schema";
import { torneoPublicoEnvelope } from "../schemas/torneo-publico.schema";

/**
 * The ONE client of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * | Route | Method | Wrapper |
 * |---|---|---|
 * | `GET /publico/competencias/encuentros` | GET | `EncuentrosPublicosOut` |
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/competencias/presentation/controllers/competencias_publico_controller.py`
 * → `CompetenciasPublicoController`): a route that is not registered does not
 * exist and is never called from here.
 *
 * The route is ANONYMOUS and of SOLO LECTURA: it publishes the encounters of
 * the published edition and it never writes.
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 */

/** The route of the public surface of the encounters. */
export const RUTA_ENCUENTROS_PUBLICOS = "/publico/competencias/estado";

/**
 * The public encounters of the published edition.
 *
 * The answer is parsed with the Zod mirror of the wrapper: a body that does
 * not comply is a LOUD failure, never a partially trusted value.
 */
export async function obtenerEncuentrosPublicos(): Promise<TorneoPublico> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_ENCUENTROS_PUBLICOS,
    undefined,
    { params: undefined },
  );

  if (status === 204) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new Error(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const envelope = torneoPublicoEnvelope.parse(data);

  if (!envelope.success || envelope.data === null) {
    throw new Error(
      envelope.message ?? "No se pudieron obtener los partidos publicados.",
    );
  }

  return envelope.data;
}
