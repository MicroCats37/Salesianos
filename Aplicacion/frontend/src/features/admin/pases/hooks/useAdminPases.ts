"use client";

import {
  type UseMutationResult,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { useState } from "react";
import { notify } from "@/errors";
import type { ErrorAdmin } from "@/features/admin/operaciones/services/admin.service";
import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import {
  type AdminCortesia,
  type AdminCortesiaRevocada,
  adminCortesiasListaEnvelope,
  type EmitirTicket,
  type OtorgarCortesia,
  type PaginaCortesias,
  type RevocarCortesia,
  type TicketEmitido,
} from "../schemas/admin.pase.schema";
import {
  emitirCredencial,
  otorgarCortesia,
  revocarCortesia,
  rutaCortesias,
} from "../services/admin.pase.service";
import {
  adminPaseClaves,
  type ParamsListaCortesias,
} from "../utils/admin.pase.claves.utils";
import { type EstadoDeFallo, estadoDeFallo } from "../utils/admin.pase.utils";

/**
 * The reads and the commands of the ADMINISTRATIVE PASSES.
 *
 * ## What a command dirties
 *
 * The invalidation is EXPLICIT and it lives INSIDE the mutation: a component
 * that unmounts while the command is in flight would never invalidate and the
 * cache would keep an answer the server never gave.
 *
 * | Command | What it dirties |
 * |---|---|
 * | the grant of a courtesy | the list of the courtesies |
 * | the revocation of a courtesy | the list of the courtesies |
 * | the issue of a credential | NOTHING: the credential is not a dataset |
 */

/** The state of the list of the courtesies, in the language of the area. */
export type EstadoListaCortesias =
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string }
  | { estado: "listo"; datos: PaginaCortesias };

/**
 * The list of the courtesies (`RT-PS-07`).
 *
 * It is an ADMINISTRATIVE LIST: it keeps the staleness of a list and not the
 * one of a catalogue.
 */
export function useAdminCortesias(params?: ParamsListaCortesias) {
  return useApiQuery({
    queryKey: adminPaseClaves.cortesias(),
    url: rutaCortesias(),
    schema: datosDelEnvelope(adminCortesiasListaEnvelope),
    params: {
      edicion_id: params?.edicion_id,
      estado: params?.estado,
      page: params?.page,
      page_size: params?.page_size,
    },
    showToast: false,
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

/**
 * The list of the courtesies, already translated into the state that the
 * panel draws.
 *
 * The error is NOT toasted here: the panel shows it, with the public prose of
 * the backend, in the place where the operator is looking.
 */
export function useEstadoCortesias(
  params?: ParamsListaCortesias,
): EstadoListaCortesias {
  const consulta = useAdminCortesias(params);

  if (consulta.isPending) {
    return { estado: "cargando" };
  }

  if (consulta.isError) {
    return { estado: "error", mensaje: consulta.error.message };
  }

  return { estado: "listo", datos: consulta.data };
}

/**
 * The grant of a courtesy (`RT-PS-08`).
 *
 * The failure is NOT toasted: the modal shows it inline, with the public
 * prose of the backend, so the operator does not have to remember what the
 * toast said.
 */
export function useOtorgarCortesia(): UseMutationResult<
  AdminCortesia,
  ErrorAdmin,
  OtorgarCortesia
> {
  const queryClient = useQueryClient();

  return useMutation<AdminCortesia, ErrorAdmin, OtorgarCortesia>({
    mutationFn: async (payload) => {
      try {
        const resultado = await otorgarCortesia(payload);
        notify.success("La cortesía se registró correctamente.");
        return resultado;
      } finally {
        await invalidateDatasets(queryClient, [adminPaseClaves.cortesias()]);
      }
    },
  });
}

/**
 * The revocation of a courtesy (`RT-PS-09`).
 *
 * The revocation is IDEMPOTENT: when the courtesy was already revoked the
 * server answers the SAME final state with `ya_revocado = true`, and the
 * interface says so instead of claiming a change that did not happen.
 */
export function useRevocarCortesia(): UseMutationResult<
  AdminCortesiaRevocada,
  ErrorAdmin,
  { cortesiaId: string; payload: RevocarCortesia }
> {
  const queryClient = useQueryClient();

  return useMutation<
    AdminCortesiaRevocada,
    ErrorAdmin,
    { cortesiaId: string; payload: RevocarCortesia }
  >({
    mutationFn: async ({ cortesiaId, payload }) => {
      try {
        const resultado = await revocarCortesia(cortesiaId, payload);
        notify.success(
          resultado.ya_revocado
            ? "La cortesía ya estaba revocada."
            : "La cortesía se revocó correctamente.",
        );
        return resultado;
      } finally {
        await invalidateDatasets(queryClient, [adminPaseClaves.cortesias()]);
      }
    },
  });
}

/** The state of the issue of a credential. */
export type EstadoCredencial = "inactiva" | "emitiendo" | "emitida" | "error";

/** The hook of the ONE-SHOT credential of the door. */
export interface UseEmitirCredencial {
  /** The state of the issue. */
  estado: EstadoCredencial;
  /** The credential that was issued: `null` until it is issued. */
  credencial: TicketEmitido | null;
  /** The failure of the last attempt, when there was one. */
  fallo: EstadoDeFallo | null;
  /** Issues the credential of ONE right. */
  emitir: (derechoId: string) => Promise<TicketEmitido | null>;
  /** Discards the credential: the secret leaves the browser. */
  descartar: () => void;
}

/**
 * The issue of the credential of the door (`RT-VT-03`).
 *
 * ## Why this hook is NOT a mutation
 *
 * The code of the credential is a SECRET that the server publishes ONCE. It
 * never enters the query cache and it never enters the mutation cache: it
 * lives in the LOCAL state of the component that shows it, and it is
 * discarded when the component closes. There is no query key, no store and no
 * shared state that could keep it alive (`F6`).
 */
export function useEmitirCredencial(): UseEmitirCredencial {
  const [credencial, setCredencial] = useState<TicketEmitido | null>(null);
  const [estado, setEstado] = useState<EstadoCredencial>("inactiva");
  const [fallo, setFallo] = useState<EstadoDeFallo | null>(null);

  async function emitir(derechoId: string): Promise<TicketEmitido | null> {
    setEstado("emitiendo");
    setFallo(null);

    try {
      const emitida = await emitirCredencial({
        derecho_id: derechoId,
      } satisfies EmitirTicket);

      setCredencial(emitida);
      setEstado("emitida");
      notify.success("La credencial se emitió correctamente.");

      return emitida;
    } catch (error) {
      setEstado("error");
      setFallo(estadoDeFallo(error));
      return null;
    }
  }

  function descartar(): void {
    setCredencial(null);
    setEstado("inactiva");
    setFallo(null);
  }

  return { estado, credencial, fallo, emitir, descartar };
}
