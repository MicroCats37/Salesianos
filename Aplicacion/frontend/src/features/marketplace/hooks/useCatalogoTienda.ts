"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import {
  listarCategorias,
  listarProductos,
} from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

/**
 * The categories of the catalogue (`RT-MK-01`).
 *
 * They are a CATALOGUE: they change with the edition, not with the second.
 */
export function useCategoriasTienda() {
  return useQuery(
    datasetQueryOptions({
      queryKey: marketplaceClaves.categorias(),
      queryFn: () => listarCategorias(),
      kind: "catalogo",
    }),
  );
}

/** The parameters that change the answer of the catalogue. */
export interface ParamsCatalogoTienda {
  /** The category that filters the catalogue, read from the URL. */
  categoria_id?: string;
  /** The page, 1-based. */
  page?: number;
  /** The size of the page. */
  page_size?: number;
}

/**
 * The catalogue of products (`RT-MK-02`).
 *
 * The filter of the category lives in the URL and it travels to the SERVER:
 * the browser never filters a catalogue on its own (`RB-02` SHOP-01).
 */
export function useCatalogoTienda(
  params?: ParamsCatalogoTienda,
  habilitado = true,
) {
  return useQuery({
    ...datasetQueryOptions({
      queryKey: marketplaceClaves.productosParams(params),
      queryFn: () => listarProductos(params),
      kind: "catalogo",
    }),
    enabled: habilitado,
  });
}
