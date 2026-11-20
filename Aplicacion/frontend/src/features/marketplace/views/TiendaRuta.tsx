"use client";

import { handleApiError } from "@/errors";
import { useCatalogoTienda, useCategoriasTienda } from "../hooks";
import type { EstadoVistaTienda } from "../types/marketplace.types";
import { TiendaCatalogoView } from "./TiendaCatalogoView";

export interface TiendaRutaProps {
  /**
   * The category of the URL, by its slug.
   *
   * The server filters by the IDENTIFIER of the category, so the slug of the
   * URL is resolved against the published categories before the catalogue is
   * asked for.
   */
  categoriaActiva?: string;
}

/**
 * The container of `SHOP-01`.
 *
 * The page (`src/app/(public)/tienda/page.tsx`) is ROUTING-ONLY: this
 * container owns the reads of the catalogue and the VIEW owns the drawing.
 *
 * The browser NEVER filters the catalogue on its own: the slug of the URL
 * becomes the identifier of the server and the server answers with the page
 * that belongs to it (`RB-02` SHOP-01).
 */
export function TiendaRuta({ categoriaActiva }: TiendaRutaProps) {
  const categorias = useCategoriasTienda();

  const categoriaId = categorias.data?.find(
    (categoria) => categoria.slug === categoriaActiva,
  )?.id;

  const hayFiltro = Boolean(categoriaActiva);
  const filtrando = hayFiltro && categoriaId !== undefined;

  const productos = useCatalogoTienda(
    filtrando ? { categoria_id: categoriaId } : undefined,
    !hayFiltro || categorias.isSuccess || categorias.isError,
  );

  const error = productos.error ? handleApiError(productos.error) : null;

  const estado: EstadoVistaTienda = productos.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : productos.data
        ? "listo"
        : "sin-datos";

  return (
    <TiendaCatalogoView
      estado={estado}
      productos={productos.data?.items}
      categorias={categorias.data}
      categoriaActiva={categoriaActiva}
      mensajeError={error?.message}
      reintentar={() => void productos.refetch()}
    />
  );
}
