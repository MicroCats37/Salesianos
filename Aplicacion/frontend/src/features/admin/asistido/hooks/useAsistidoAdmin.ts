"use client";

import {
  type UseMutationResult,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { notify } from "@/errors";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { marketplaceClaves } from "@/features/marketplace/utils/marketplace.claves.utils";
import { paseClaves } from "@/features/pases/utils/pase.claves.utils";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import {
  agregarParticipanteEquipo,
  comprarPaseCliente,
  comprarPedidoCliente,
} from "../services/asistido.service";
import type {
  AgregarParticipanteEquipoIn,
  CompraAsistidaOut,
  ComprarPaseClienteIn,
  ComprarPedidoClienteIn,
  ParticipanteAsistidoOut,
} from "../types/asistido.types";

/**
 * The commands of the ADMINISTRATIVE ASSISTED area.
 *
 * ## What a command dirties
 *
 * The invalidation is EXPLICIT and it lives INSIDE the mutation
 * (`FND-08` §3 regla 5): a component that unmounts while the command is in
 * flight would never invalidate and the cache would keep an answer the
 * server never gave.
 *
 * | Command | What it dirties |
 * |---|---|
 * | the add of a participant | the teams, the participants and the registrations of the area |
 * | the assisted purchase of passes | the payments of the area and the purchases of passes |
 * | the assisted order of the store | the payments of the area, the catalogue, the inventory and the orders |
 */

/** The command that adds an existing participant to a team. */
export function useAgregarParticipanteEquipo(): UseMutationResult<
  ParticipanteAsistidoOut,
  Error,
  { equipoId: string; payload: AgregarParticipanteEquipoIn }
> {
  const queryClient = useQueryClient();

  return useMutation<
    ParticipanteAsistidoOut,
    Error,
    { equipoId: string; payload: AgregarParticipanteEquipoIn }
  >({
    mutationFn: async ({ equipoId, payload }) => {
      try {
        const resultado = await agregarParticipanteEquipo(equipoId, payload);
        notify.success("El participante se agregó al equipo correctamente.");
        return resultado;
      } catch (error) {
        notify.error(
          error instanceof Error
            ? error.message
            : "No se pudo agregar al participante.",
        );
        throw error;
      } finally {
        await invalidateDatasets(queryClient, [
          adminClaves.equipos.all,
          adminClaves.participantes.all,
          adminClaves.inscripciones.all,
        ]);
      }
    },
  });
}

/** The command that buys passes for a client and registers its payment. */
export function useComprarPaseCliente(): UseMutationResult<
  CompraAsistidaOut,
  Error,
  ComprarPaseClienteIn
> {
  const queryClient = useQueryClient();

  return useMutation<CompraAsistidaOut, Error, ComprarPaseClienteIn>({
    mutationFn: async (payload) => {
      try {
        const resultado = await comprarPaseCliente(payload);
        notify.success(
          "La compra de pases para el cliente se registró correctamente.",
        );
        return resultado;
      } catch (error) {
        notify.error(
          error instanceof Error
            ? error.message
            : "No se pudo registrar la compra de pases.",
        );
        throw error;
      } finally {
        await invalidateDatasets(queryClient, [
          adminClaves.pagos.all,
          paseClaves.compras(),
        ]);
      }
    },
  });
}

/** The command that orders the store for a client and registers its payment. */
export function useComprarPedidoCliente(): UseMutationResult<
  CompraAsistidaOut,
  Error,
  ComprarPedidoClienteIn
> {
  const queryClient = useQueryClient();

  return useMutation<CompraAsistidaOut, Error, ComprarPedidoClienteIn>({
    mutationFn: async (payload) => {
      try {
        const resultado = await comprarPedidoCliente(payload);
        notify.success("El pedido para el cliente se registró correctamente.");
        return resultado;
      } catch (error) {
        notify.error(
          error instanceof Error
            ? error.message
            : "No se pudo registrar el pedido.",
        );
        throw error;
      } finally {
        await invalidateDatasets(queryClient, [
          adminClaves.pagos.all,
          marketplaceClaves.todas,
        ]);
      }
    },
  });
}
