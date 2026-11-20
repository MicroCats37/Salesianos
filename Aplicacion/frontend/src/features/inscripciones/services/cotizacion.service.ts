import { apiSend } from "@/lib/api";
import {
  type Cotizacion,
  type CotizacionIn,
  cotizacionInSchema,
  cotizacionOutSchema,
} from "../schemas/cotizacion.schema";
import type { Respuesta } from "./respuesta.service";
import { leerRespuesta } from "./respuesta.service";

/**
 * The transport of the QUOTATION of the registration area.
 *
 * Backend: `CotizacionController` of `modules/salesianos_fest`, restored by
 * `restore-registration-promotion-catalog-flow`.
 *
 * | Route | Method | Presenter | Wrapper |
 * |---|---|---|---|
 * | `POST /cotizaciones` | POST | the quotation of the catalogue | `CotizacionOut` |
 *
 * The quotation is a STATELESS calculation of the server against the
 * catalogue in force (`RN-C02`). It is not persisted: it belongs to the
 * wizard session and it travels back to the server as a CONCURRENCY TOKEN
 * (`version`), so a price that moved between the quotation and the alta is
 * detected instead of silently accepted.
 *
 * The URL is the one of the frozen tree without the trailing slash, the
 * style of the target controllers: no trailing slash and NO other route.
 */

/** The route of the quotation. */
export const RUTA_COTIZACIONES = "/cotizaciones";

/**
 * The quotation of a package and a quantity.
 *
 * The request is validated BEFORE it leaves the browser: a quantity below 1
 * is a form error and not a round trip.
 */
export async function cotizarPaquete(
  payload: CotizacionIn,
): Promise<Respuesta<Cotizacion>> {
  const entrada = cotizacionInSchema.parse(payload);

  const { status, data } = await apiSend<unknown>(
    "post",
    RUTA_COTIZACIONES,
    entrada,
  );

  if (status === 204) {
    throw new Error("La cotización respondió sin contenido.");
  }

  return leerRespuesta(
    cotizacionOutSchema,
    data,
    "El servidor no devolvió la cotización del paquete.",
  );
}
