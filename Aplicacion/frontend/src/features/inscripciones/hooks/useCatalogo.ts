"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import type {
  CatalogoDisciplinas,
  CatalogoPaquetes,
} from "../schemas/catalogo.schema";
import {
  obtenerCatalogoDisciplinas,
  obtenerCatalogoPaquetes,
} from "../services/catalogo.service";
import {
  clavesCatalogoDisciplinas,
  clavesCatalogoPaquetes,
} from "../utils/inscripcion.claves.utils";
import { leerConEstado } from "../utils/inscripcion.errores.utils";

/**
 * The reads of the catalogue of the edition.
 *
 * `GET /catalogo/paquetes` (`RT-IN-12`) and `GET /catalogo/disciplinas`
 * (`RT-IN-13`), the two routes that the target backend registers.
 *
 * The catalogue is a CATALOGUE: it changes by decision of the organization
 * and not by the minute, so its staleness is the one of the data contract
 * for catalogues (ten minutes) and its lifetime in the cache is never
 * shorter than that.
 *
 * The edition is the only parameter that changes the answer, and it travels
 * in the key (`inscripcion.claves.utils.ts`).
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
