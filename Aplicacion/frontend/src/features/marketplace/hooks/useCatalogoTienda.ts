"use client";

import { useApiCreate, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type {
  ProductoCreado,
  ProductoCrearFormData,
  ProductoCrearPayload,
} from "../schemas/producto.schema";
import {
  categoriasEnvelope,
  productoCreadoEnvelope,
  productosEnvelope,
} from "../schemas/producto.schema";
import { rutaCategorias, rutaProductos } from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

/**
 * The categories of the catalogue (`RT-MK-01`).
 *
 * They are a CATALOGUE: they change with the edition, not with the second.
 */
export function useCategoriasTienda() {
  return useApiQuery({
    queryKey: marketplaceClaves.categorias(),
    url: rutaCategorias(),
    schema: datosDelEnvelope(categoriasEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}

/** The parameters that change the answer of the catalogue. */
export type ParamsCatalogoTienda = {
  /** The category that filters the catalogue, read from the URL. */
  categoria_id?: string;
  /** The page, 1-based. */
  page?: number;
  /** The size of the page. */
  page_size?: number;
};

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
  return useApiQuery({
    queryKey: marketplaceClaves.productos(),
    url: rutaProductos(),
    schema: datosDelEnvelope(productosEnvelope),
    params,
    queryOptions: {
      enabled: habilitado,
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}

/** Creates a product and refreshes every public store projection. */
export function useCrearProducto() {
  const crear = useApiCreate<ProductoCreado, ProductoCrearPayload>({
    url: rutaProductos(),
    schema: datosDelEnvelope(productoCreadoEnvelope),
    invalidateKeys: [marketplaceClaves.todas],
  });

  return {
    ...crear,
    mutateAsync: (datos: ProductoCrearFormData) =>
      crear.mutateAsync({
        nombre: datos.nombre,
        slug: datos.slug,
        descripcion: datos.descripcion,
        categoria_id: datos.categoria_id,
        precio: datos.precio,
        precio_oferta: datos.precio_oferta,
        oferta_inicia: datos.oferta_inicia,
        oferta_termina: datos.oferta_termina,
        estado: datos.estado,
        imagenes: datos.imagenes.map((imagen) => ({
          token: imagen.archivo,
          texto_alternativo: imagen.texto_alternativo,
          es_principal: imagen.es_principal,
        })),
      }),
  };
}
