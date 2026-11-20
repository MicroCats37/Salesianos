import { apiSend } from "@/lib/api";
import {
  type CatalogoCategorias,
  type CatalogoDisciplinas,
  type CatalogoPaquetes,
  type CatalogoPromociones,
  catalogoCategoriasSchema,
  catalogoDisciplinasSchema,
  catalogoPaquetesSchema,
  catalogoPromocionesSchema,
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
 * | `GET /catalogo/promociones` | `RT-IN-15` | GET | `CatalogoPresenter.present_promociones` | `CatalogoPromocionesOut` |
 * | `GET /catalogo/categorias` | `RT-IN-16` | GET | `CatalogoPresenter.present_categorias` | `CatalogoCategoriasOut` |
 *
 * The URLs are the ones of the TARGET controller: no trailing slash (the
 * frozen tree used one) and NO other route.
 *
 * The catalogue is PUBLIC (`AllowAny`): a visitor chooses the package before
 * creating an account, so the read cannot require a session.
 *
 * `edicion_id` is OPTIONAL: when it is omitted the server resolves the
 * edition with the frozen resolution order (`FR-02` §2.2). The edition is
 * the only parameter that changes the answer, and it travels in the key.
 *
 * ## This client is THE client of the catalogue
 *
 * ONE endpoint, ONE client (`salesianos-api-data`): the public portada and
 * the competitions area read the SAME catalogue through THIS module instead
 * of declaring a second client and a second key namespace for the same
 * answer (FND-08, rule 1).
 */

/** The route of the catalogue of packages (`RT-IN-12`). */
export const RUTA_CATALOGO_PAQUETES = "/catalogo/paquetes";

/** The route of the catalogue of disciplines (`RT-IN-13`). */
export const RUTA_CATALOGO_DISCIPLINAS = "/catalogo/disciplinas";

/** The route of the catalogue of cohorts (`RT-IN-15`). */
export const RUTA_CATALOGO_PROMOCIONES = "/catalogo/promociones";

/** The route of the catalogue of competitive bands (`RT-IN-16`). */
export const RUTA_CATALOGO_CATEGORIAS = "/catalogo/categorias";

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

/**
 * The catalogue of COHORTS of the edition (`RT-IN-15`).
 *
 * The cohort is the year that the visitor selects explicitly when the
 * registration is created: it is the input from which the server derives the
 * competitive band of the teams.
 *
 * @param edicionId the edition of the scope. When it is omitted the server
 * resolves it with the frozen order.
 */
export async function obtenerCatalogoPromociones(
  edicionId?: string,
): Promise<Respuesta<CatalogoPromociones>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_CATALOGO_PROMOCIONES,
    undefined,
    { params: edicionId ? { edicion_id: edicionId } : undefined },
  );

  if (status === 204) {
    throw new Error("El catálogo de promociones respondió sin contenido.");
  }

  return leerRespuesta(
    catalogoPromocionesSchema,
    data,
    "El servidor no devolvió el catálogo de promociones.",
  );
}

/**
 * The catalogue of COMPETITIVE BANDS of the edition (`RT-IN-16`).
 *
 * The band is DECLARED with the range of cohorts that it covers. The browser
 * prints the declaration and NEVER derives which band a cohort belongs to:
 * that resolution belongs to the server (`RN-C02`, `QA-K01`).
 *
 * @param edicionId the edition of the scope. When it is omitted the server
 * resolves it with the frozen order.
 */
export async function obtenerCatalogoCategorias(
  edicionId?: string,
): Promise<Respuesta<CatalogoCategorias>> {
  const { status, data } = await apiSend<unknown>(
    "get",
    RUTA_CATALOGO_CATEGORIAS,
    undefined,
    { params: edicionId ? { edicion_id: edicionId } : undefined },
  );

  if (status === 204) {
    throw new Error("El catálogo de categorías respondió sin contenido.");
  }

  return leerRespuesta(
    catalogoCategoriasSchema,
    data,
    "El servidor no devolvió el catálogo de categorías.",
  );
}
