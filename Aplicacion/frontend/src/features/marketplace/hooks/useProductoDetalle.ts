"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { obtenerProducto } from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

/**
 * The detail of a product (`RT-MK-03`).
 *
 * The slug is the identity of the product in the URL. The read is DISABLED
 * when there is no slug: the frontend never calls a route it cannot open.
 */
export function useProductoDetalle(slug: string | undefined) {
  return useQuery({
    ...datasetQueryOptions({
      queryKey: marketplaceClaves.detalle(slug ?? ""),
      queryFn: () => obtenerProducto(slug as string),
      kind: "catalogo",
    }),
    enabled: Boolean(slug),
  });
}
