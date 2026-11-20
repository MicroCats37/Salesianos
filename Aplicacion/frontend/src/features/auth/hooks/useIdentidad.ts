"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  confirmarPersona,
  consultarDocumento,
  resolverPersona,
} from "../services/identidad.service";
import { authClaves } from "../utils/auth.claves.utils";

/**
 * The identity mutations.
 *
 * They own the INVALIDATION of the data they affect and NOTHING else: the
 * read of a session is not repeated because somebody looked up a document, and
 * the catalogue is not invalidated because an identity was confirmed.
 */

/**
 * `RT-ID-01` — consults a document in the external identity source.
 *
 * The consultation does NOT create a person and it does NOT authorise
 * anything: it only answers what the source publishes about a document.
 */
export function useConsultaDocumento() {
  return useMutation({
    mutationFn: (documento: string) => consultarDocumento(documento),
  });
}

/**
 * `RT-ID-02` — resolves an identity, local first.
 *
 * The invalidation is EXACT: the key of the resolved document, and nothing
 * else.
 */
export function useResolverPersona() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resolverPersona,
    onSuccess: (persona) => {
      queryClient.invalidateQueries({
        queryKey: authClaves.personaResuelta(
          persona.tipo_documento,
          persona.numero_documento,
        ),
      });
    },
  });
}

/**
 * `RT-ID-03` — confirms and persists an identity.
 *
 * Confirming an identity links the person to the account, so the FACTS OF THE
 * SESSION are the only data that becomes stale: the session key and the
 * identity namespace are invalidated, and nothing else is touched.
 */
export function useConfirmarPersona() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: confirmarPersona,
    onSuccess: (persona) => {
      queryClient.invalidateQueries({ queryKey: authClaves.sesion() });
      queryClient.invalidateQueries({
        queryKey: authClaves.personaConfirmada(
          persona.tipo_documento,
          persona.numero_documento,
        ),
      });
    },
  });
}
