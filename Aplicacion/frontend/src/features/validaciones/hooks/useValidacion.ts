"use client";

import type { MutateOptions } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { z } from "zod";
import { useApiCreate } from "@/hooks/callsApi/useApiCreate";
import type {
  ConfirmarTicketDatos,
  PreviewTicketDatos,
  TicketConfirmado,
  TicketPreview,
} from "../schemas/validacion.schema";
import {
  ticketConfirmadoEnvelope,
  ticketPreviewEnvelope,
} from "../schemas/validacion.schema";
import { ErrorContratoValidacion } from "../services/validacion.service";

/**
 * The base of every validation route.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/validaciones/presentation/controllers/validacion_controller.py`
 * → `ValidacionController`): a route that is not registered does not exist and
 * is never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-RT-01` | POST | `/validaciones/preview` | `TicketPreviewOut` |
 * | `RT-RT-02` | POST | `/validaciones/confirmar` | `TicketConfirmadoOut` |
 */
const BASE = "/validaciones";

/**
 * The Zod mirror of the envelope of the area, as a schema that OPENS it.
 *
 * It applies the SAME rules that the transport of the area applied: a body
 * that does not comply with the mirror is a loud failure and a body that
 * opens but carries no data is a failure too. The mirror itself is the one
 * of the area (`validacion.schema.ts`): it is not duplicated here.
 */
function envelopeDeDatos<T>(
  envelope: z.ZodType<{ success: boolean; data: T | null }>,
): z.ZodType<T, unknown> {
  return z.unknown().transform((body) => {
    const parseado = envelope.safeParse(body);

    if (!parseado.success) {
      throw new ErrorContratoValidacion(
        "La respuesta del servidor no cumple el contrato esperado.",
        parseado.error,
      );
    }

    if (!parseado.data.success || parseado.data.data === null) {
      throw new ErrorContratoValidacion("El servidor respondió sin datos.");
    }

    return parseado.data.data;
  });
}

/**
 * The CHECK of a credential (`RT-RT-01`).
 *
 * It is a MUTATION and not a query: the credential is a secret that travels in
 * the body, and a cache would keep it in memory and could publish it in a
 * later request. The check does NOT consume (`RN-P06`).
 *
 * The public contract is unchanged: the caller still hands over the CODE and
 * receives the preview of the credential. The route and the body are the ones
 * of the ledger, and the credential travels in the body of the POST, never in
 * the query string.
 */
export function usePreviewTicket() {
  const mutation = useApiCreate<TicketPreview, PreviewTicketDatos>({
    url: `${BASE}/preview`,
    schema: envelopeDeDatos(ticketPreviewEnvelope),
  });

  return {
    ...mutation,
    mutate: (
      codigo: string,
      options?: MutateOptions<TicketPreview, AxiosError, PreviewTicketDatos>,
    ) => mutation.mutate({ codigo }, options),
    mutateAsync: (codigo: string) => mutation.mutateAsync({ codigo }),
  };
}

/**
 * The CONFIRMATION of a credential (`RT-RT-02`).
 *
 * The caller owns the `idempotency_key`: repeating the SAME key returns the
 * same record and never consumes twice (`FR-04` §2.2). The body of the
 * request IS the payload of the canje, so the variables of the mutation
 * travel as they are.
 */
export function useConfirmarTicket() {
  return useApiCreate<TicketConfirmado, ConfirmarTicketDatos>({
    url: `${BASE}/confirmar`,
    schema: envelopeDeDatos(ticketConfirmadoEnvelope),
  });
}
