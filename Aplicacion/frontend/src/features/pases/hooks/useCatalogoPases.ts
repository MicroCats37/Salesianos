"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { listarPases } from "../services/pase.service";
import { paseClaves } from "../utils/pase.claves.utils";

/**
 * The parameters that change the answer of the catalogue.
 *
 * The edition is resolved by the server when it is not declared, following
 * the frozen order of `FR-02` §2.2. It travels in the key when it is
 * declared, so two editions are two cache entries.
 */
export interface ParamsCatalogoPases {
  edicion_id?: string;
}

/**
 * The catalogue of the passes of the edition in scope (`RT-PS-01`).
 *
 * It is a CATALOGUE: it changes with the edition, not with the second, so it
 * keeps the staleness of a catalogue and NOT the one of a commercial state.
 */
export function useCatalogoPases(params?: ParamsCatalogoPases) {
  return useQuery(
    datasetQueryOptions({
      queryKey: paseClaves.catalogoParams(params),
      queryFn: () => listarPases(params),
      kind: "catalogo",
    }),
  );
}
