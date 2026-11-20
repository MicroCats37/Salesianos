import { apiSend } from "@/lib/api";
import {
  type CompraCreada,
  type ComprarCuposIn,
  compraCreadaSchema,
} from "../schemas/compra-cupos.schema";
import {
  type InscripcionDetalle,
  type InscripcionInicial,
  type InscripcionInicialIn,
  inscripcionDetalleSchema,
  inscripcionInicialSchema,
} from "../schemas/inscripcion.schema";
import {
  type ParticipanteAsignarIn,
  type Pool,
  poolSchema,
} from "../schemas/pool.schema";
import type { Respuesta } from "./respuesta.service";
import { leerRespuesta } from "./respuesta.service";

/**
 * The transport of the registrations of the TARGET backend.
 *
 * Backend: `InscripcionController` (packets DOM-01 and DOM-02), registered
 * in `Aplicacion/backend/config/api.py`.
 *
 * | Route | Ledger | Method | Presenter | Wrapper |
 * |---|---|---|---|---|
 * | `POST /inscripciones` | `RT-IN-14` | POST | `InscripcionPresenter.present_inicial` | `InscripcionInicialOut` |
 * | `GET /inscripciones/{id}` | `RT-IN-02` | GET | `InscripcionPresenter.present_detalle` | `InscripcionDetalleOut` |
 * | `GET /inscripciones/{id}/equipos` | `RT-IN-04` | GET | `InscripcionPresenter.present_equipos` | `EquiposInscripcionOut` |
 * | `GET /inscripciones/{id}/pool` | `RT-IN-03` | GET | `PoolPresenter.present_pool` | `PoolOut` |
 * | `POST /inscripciones/{id}/participantes` | `RT-IN-05` | POST | `PoolPresenter.present_pool` | `PoolOut` |
 * | `DELETE /inscripciones/{id}/participantes/{participacion_id}` | `RT-IN-06` | DELETE | `PoolPresenter.present_pool` | `PoolOut` |
 * | `POST /inscripciones/{id}/compras/cupos` | `RT-CM-01` | POST | `CompraCuposPresenter.present_compra` | `CompraCreadaOut` |
 *
 * Three of the seven routes publish the SAME wrapper `PoolOut`: adding a
 * participant, moving one and removing one answer with the UPDATED pool. That
 * is what lets the browser write the answer into the cache instead of
 * guessing the new balance (`RN-I04`).
 *
 * There is NO route that lists the purchases of a registration and NO route
 * that lists the inscriptions of the responsible: neither is invented here.
 */

/** The root of the routes of the inscriptions. */
export const RUTA_INSCRIPCIONES = "/inscripciones";

/**
 * The alta of a registration and of its PENDING purchase (`RT-IN-14`).
 *
 * The retry does NOT create a second inscription and does NOT open a second
 * purchase: the server answers with the inscription that already exists and
 * with its pending purchase (`FR-04` I-4).
 */
export async function crearInscripcionInicial(
  payload: InscripcionInicialIn,
): Promise<Respuesta<InscripcionInicial>> {
  const { status, data } = await apiSend<unknown>(
    "post",
    RUTA_INSCRIPCIONES,
    payload,
  );

  if (status === 204) {
    throw new Error("El alta de la inscripción respondió sin contenido.");
  }

  return leerRespuesta(
    inscripcionInicialSchema,
    data,
    "El servidor no devolvió la inscripción recién registrada.",
  );
}

/**
 * The detail of a registration and its balance of cupos (`RT-IN-02`).
 *
 * The wrapper already publishes the teams of the registration
 * (`InscripcionDetalleOut.equipos`), so the teams have ONE owner in the
 * cache: this read. The route `GET /inscripciones/{id}/equipos` (`RT-IN-04`)
 * exists and is registered, but it is NOT bound here: binding both would
 * give the teams of a registration two cache entries and two sources of
 * truth (FND-08, rule 1).
 */
export async function obtenerInscripcion(
  inscripcionId: string,
): Promise<Respuesta<InscripcionDetalle>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    `${RUTA_INSCRIPCIONES}/${inscripcionId}`,
  );

  if (status === 204) {
    throw new Error("El detalle de la inscripción respondió sin contenido.");
  }

  return leerRespuesta(
    inscripcionDetalleSchema,
    data,
    "El servidor no devolvió el detalle de la inscripción.",
  );
}

/**
 * The pool of cupos of a registration (`RT-IN-03`).
 *
 * The three counters and the impediments are the answer of the server
 * (`RN-I03`): the browser prints them and never subtracts them.
 */
export async function obtenerPool(
  inscripcionId: string,
): Promise<Respuesta<Pool>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    `${RUTA_INSCRIPCIONES}/${inscripcionId}/pool`,
  );

  if (status === 204) {
    throw new Error("El pool de la inscripción respondió sin contenido.");
  }

  return leerRespuesta(
    poolSchema,
    data,
    "El servidor no devolvió el pool de la inscripción.",
  );
}

/**
 * Adds a participant to the pool, or MOVES one (`RT-IN-05`).
 *
 * With `reemplaza_participacion_id` the operation is a MOVEMENT: the new
 * person takes over the cupo of the withdrawn one and both happen in the
 * same transaction (`FL-05` step 4, `RN-I04`).
 *
 * The answer is the UPDATED pool.
 */
export async function agregarParticipante(
  inscripcionId: string,
  payload: ParticipanteAsignarIn,
): Promise<Respuesta<Pool>> {
  const { status, data } = await apiSend<unknown>(
    "post",
    `${RUTA_INSCRIPCIONES}/${inscripcionId}/participantes`,
    payload,
  );

  if (status === 204) {
    throw new Error("El pool de la inscripción respondió sin contenido.");
  }

  return leerRespuesta(
    poolSchema,
    data,
    "El servidor no devolvió el pool de la inscripción.",
  );
}

/**
 * Withdraws a participant and frees its cupo (`RT-IN-06`).
 *
 * Withdrawing frees the cupo of THAT registration and does NOT cancel the
 * purchase, does NOT return money and does NOT touch the inventory
 * (`RN-I04`, `DEC-06`).
 *
 * The answer is the UPDATED pool.
 */
export async function retirarParticipante(
  inscripcionId: string,
  participacionId: string,
): Promise<Respuesta<Pool>> {
  const { status, data } = await apiSend<unknown>(
    "delete",
    `${RUTA_INSCRIPCIONES}/${inscripcionId}/participantes/${participacionId}`,
  );

  if (status === 204) {
    throw new Error("El pool de la inscripción respondió sin contenido.");
  }

  return leerRespuesta(
    poolSchema,
    data,
    "El servidor no devolvió el pool de la inscripción.",
  );
}

/**
 * The purchase of EXTRA cupos of a registration (`RT-CM-01`).
 *
 * The price is NOT declared by the client: the server resolves it against
 * the catalogue in force (`RN-C02`). The purchase stays `PENDIENTE` and the
 * cupos are enabled when the payment is confirmed (`RN-I02`).
 *
 * A retry with the same quantity returns the SAME pending purchase
 * (`FR-04` I-4).
 */
export async function comprarCupos(
  inscripcionId: string,
  payload: ComprarCuposIn,
): Promise<Respuesta<CompraCreada>> {
  const { status, data } = await apiSend<unknown>(
    "post",
    `${RUTA_INSCRIPCIONES}/${inscripcionId}/compras/cupos`,
    payload,
  );

  if (status === 204) {
    throw new Error("La compra de cupos respondió sin contenido.");
  }

  return leerRespuesta(
    compraCreadaSchema,
    data,
    "El servidor no devolvió la compra de cupos.",
  );
}
