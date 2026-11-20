"use client";

import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { productoDetalleEnvelope } from "../schemas/producto.schema";
import { rutaProductoDetalle } from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

const DETALLE_TIMEOUT_MS = 12_000;

/**
 * The detail of a product (`RT-MK-03`).
 *
 * The slug is the identity of the product in the URL. The read is DISABLED
 * when there is no slug: the frontend never calls a route it cannot open.
 */
export function useProductoDetalle(slug: string | undefined) {
  return useApiQuery({
    queryKey: marketplaceClaves.detalle(slug ?? ""),
    url: slug ? rutaProductoDetalle(slug) : null,
    schema: datosDelEnvelope(productoDetalleEnvelope),
    config: { timeout: DETALLE_TIMEOUT_MS },
    queryOptions: {
      enabled: Boolean(slug),
      // A product route must leave the pending state after one bounded attempt.
      retry: false,
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}
