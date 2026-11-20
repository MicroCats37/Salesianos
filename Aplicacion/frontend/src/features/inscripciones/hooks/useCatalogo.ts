"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import type {
  CatalogoCategorias,
  CatalogoDisciplinas,
  CatalogoPaquetes,
  CatalogoPromociones,
} from "../schemas/catalogo.schema";
import {
  obtenerCatalogoCategorias,
  obtenerCatalogoDisciplinas,
  obtenerCatalogoPaquetes,
  obtenerCatalogoPromociones,
} from "../services/catalogo.service";
import {
  clavesCatalogoCategorias,
  clavesCatalogoDisciplinas,
  clavesCatalogoPaquetes,
  clavesCatalogoPromociones,
} from "../utils/inscripcion.claves.utils";
import { leerConEstado } from "../utils/inscripcion.errores.utils";

/**
 * The reads of the catalogue of the edition.
 *
 * `GET /catalogo/paquetes` (`RT-IN-12`), `GET /catalogo/disciplinas`
 * (`RT-IN-13`), `GET /catalogo/promociones` (`RT-IN-15`) and
 * `GET /catalogo/categorias` (`RT-IN-16`).
 *
 * The catalogue is a CATALOGUE: it changes by decision of the organization
 * and not by the minute, so its staleness is the one of the data contract
 * for catalogues (ten minutes) and its lifetime in the cache is never
 * shorter than that.
 *
 * The edition is the only parameter that changes the answer, and it travels
 * in the key (`inscripcion.claves.utils.ts`).
 *
 * ## This module is THE owner of the catalogue of the edition
 *
 * The public portada and the competitions area read the same catalogue
 * through these hooks instead of declaring a second client and a second key
 * namespace for the same answer (FND-08, rule 1).
 */

/** The parameters of a read of the catalogue. */
export interface ConsultaCatalogoParams {
  /**
   * The edition of the scope. When it is omitted the server resolves it
   * with the frozen resolution order (`FR-02` §2.2).
   */
  edicion_id?: string;
}

/** The packages of the edition. */
export function useCatalogoPaquetes(params: ConsultaCatalogoParams = {}) {
  return useQuery(
    datasetQueryOptions<CatalogoPaquetes>({
      queryKey: clavesCatalogoPaquetes.listPage(params),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerCatalogoPaquetes(params.edicion_id);
          return respuesta.data;
        }),
      kind: "catalogo",
    }),
  );
}

/** The disciplines of the edition. */
export function useCatalogoDisciplinas(params: ConsultaCatalogoParams = {}) {
  return useQuery(
    datasetQueryOptions<CatalogoDisciplinas>({
      queryKey: clavesCatalogoDisciplinas.listPage(params),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerCatalogoDisciplinas(params.edicion_id);
          return respuesta.data;
        }),
      kind: "catalogo",
    }),
  );
}

/**
 * The cohorts of the edition.
 *
 * They are the years that the visitor EXPLICITLY selects when the
 * registration is created.
 */
export function useCatalogoPromociones(params: ConsultaCatalogoParams = {}) {
  return useQuery(
    datasetQueryOptions<CatalogoPromociones>({
      queryKey: clavesCatalogoPromociones.listPage(params),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerCatalogoPromociones(params.edicion_id);
          return respuesta.data;
        }),
      kind: "catalogo",
    }),
  );
}

/**
 * The competitive bands of the edition.
 *
 * The browser PRINTS the declared range of every band and never derives
 * which band a cohort belongs to: that resolution belongs to the server
 * (`RN-C02`, `QA-K01`).
 */
export function useCatalogoCategorias(params: ConsultaCatalogoParams = {}) {
  return useQuery(
    datasetQueryOptions<CatalogoCategorias>({
      queryKey: clavesCatalogoCategorias.listPage(params),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerCatalogoCategorias(params.edicion_id);
          return respuesta.data;
        }),
      kind: "catalogo",
    }),
  );
}
