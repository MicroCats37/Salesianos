import { apiSend } from "@/lib/api";
import {
  type CatalogoDisciplinas,
  type CatalogoPaquetes,
  catalogoDisciplinasSchema,
  catalogoPaquetesSchema,
} from "../schemas/catalogo.schema";
import type { Respuesta } from "./respuesta.service";
import { leerRespuesta } from "./respuesta.service";

/**
 * The transport of the catalogue of the registration area.
 *
 * Backend: `CatalogoController` (packet DOM-01), registered in
 * `Aplicacion/backend/config/api.py`.
 *
 * | Route | Ledger | Method | Presenter | Wrapper |
 * |---|---|---|---|---|
 * | `GET /catalogo/paquetes` | `RT-IN-12` | GET | `CatalogoPresenter.present_paquetes` | `CatalogoPaquetesOut` |
 * | `GET /catalogo/disciplinas` | `RT-IN-13` | GET | `CatalogoPresenter.present_disciplinas` | `CatalogoDisciplinasOut` |
 *
 * The URLs are the ones of the TARGET controller: no trailing slash (the
 * frozen tree used one) and NO other route. The target backend publishes
 * NO route for the promotions and NO route for the categories: the frozen
 * calls to those two collections are GONE and no replacement was invented.
 *
 * The catalogue is PUBLIC (`AllowAny`): a visitor chooses the package before
 * creating an account, so the read cannot require a session.
 *
 * `edicion_id` is OPTIONAL: when it is omitted the server resolves the
 * edition with the frozen resolution order (`FR-02` §2.2). The edition is
 * the only parameter that changes the answer, and it travels in the key.
 */

/** The route of the catalogue of packages (`RT-IN-12`). */
export const RUTA_CATALOGO_PAQUETES = "/catalogo/paquetes";

/** The route of the catalogue of disciplines (`RT-IN-13`). */
export const RUTA_CATALOGO_DISCIPLINAS = "/catalogo/disciplinas";

/**
 * The catalogue of packages of the edition.
 *
 * @param edicionId the edition of the scope. When it is omitted the server
 * resolves it with the frozen order.
 */
export async function obtenerCatalogoPaquetes(
  edicionId?: string,
): Promise<Respuesta<CatalogoPaquetes>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_CATALOGO_PAQUETES,
    undefined,
    { params: edicionId ? { edicion_id: edicionId } : undefined },
  );

  if (status === 204) {
    throw new Error("El catálogo de paquetes respondió sin contenido.");
  }

  return leerRespuesta(
    catalogoPaquetesSchema,
    data,
    "El servidor no devolvió el catálogo de paquetes.",
  );
}

/**
 * The catalogue of disciplines of the edition.
 *
 * @param edicionId the edition of the scope. When it is omitted the server
 * resolves it with the frozen order.
 */
export async function obtenerCatalogoDisciplinas(
  edicionId?: string,
): Promise<Respuesta<CatalogoDisciplinas>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_CATALOGO_DISCIPLINAS,
    undefined,
    { params: edicionId ? { edicion_id: edicionId } : undefined },
  );

  if (status === 204) {
    throw new Error("El catálogo de disciplinas respondió sin contenido.");
  }

  return leerRespuesta(
    catalogoDisciplinasSchema,
    data,
    "El servidor no devolvió el catálogo de disciplinas.",
  );
}
