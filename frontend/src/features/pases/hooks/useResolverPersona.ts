"use client";

import { useMutation } from "@tanstack/react-query";
import { notify } from "@/errors";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { PersonaResuelta } from "../schemas";
import { resolverPersona } from "../services";

/**
 * The mutation that resolves an EXISTING `Persona` by her civil identity.
 *
 * The lookup is a USER ACTION (the buyer types a document), so it is a
 * mutation and not a query: the cache never holds a "last searched person".
 */

/** Variables of the resolution. */
export interface VariablesResolverPersona {
  /** Document type (DNI, CE, PAS). */
  tipoDocumento: string;
  /** Document number of the person. */
  numeroDocumento: string;
}

/**
 * Resolve the person that matches the document EXACTLY.
 *
 * A 404 is NOT a failure: it means that no registered person matches, and
 * the component renders the "not found" state instead of an error. Every
 * other failure reaches the buyer through the toast adapter.
 */
export function useResolverPersona() {
  return useMutation<PersonaResuelta, ApiQueryError, VariablesResolverPersona>({
    mutationFn: (variables) =>
      resolverPersona(variables.tipoDocumento, variables.numeroDocumento),
    onError: (error) => {
      if (error.status === 404) return;
      notify.error(error.message);
    },
  });
}
