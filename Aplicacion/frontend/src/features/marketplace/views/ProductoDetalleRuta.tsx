"use client";

import { handleApiError } from "@/errors";
import { useProductoDetalle } from "../hooks";
import type { EstadoVistaTienda } from "../types/marketplace.types";
import { ProductoDetalleView } from "./ProductoDetalleView";

export interface ProductoDetalleRutaProps {
  /** The slug of the product, the identity in the URL. */
  slug: string;
}

/**
 * The container of `SHOP-02`.
 *
 * The page (`src/app/(public)/tienda/[slug]/page.tsx`) is ROUTING-ONLY: this
 * container owns the read of the product and the VIEW owns the drawing.
 *
 * The price, the offer and the gallery are the ones the server published: the
 * browser never recomputes them (`RB-02` SHOP-02).
 */
export function ProductoDetalleRuta({ slug }: ProductoDetalleRutaProps) {
  const consulta = useProductoDetalle(slug);

  const error = consulta.error ? handleApiError(consulta.error) : null;

  const estado: EstadoVistaTienda = consulta.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : consulta.data
        ? "listo"
        : "sin-datos";

  return (
    <ProductoDetalleView
      slug={slug}
      estado={estado}
      producto={consulta.data}
      mensajeError={error?.message}
      reintentar={() => void consulta.refetch()}
    />
  );
}
