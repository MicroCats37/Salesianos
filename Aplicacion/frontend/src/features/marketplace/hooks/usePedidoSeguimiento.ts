"use client";

import { useApiCreate, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type {
  IzipayConfirmacionPedido,
  IzipayPreparacionPedido,
  PagoConfirmadoPedido,
} from "../schemas/pedido.schema";
import {
  izipayPreparacionPedidoEnvelope,
  pagoConfirmadoPedidoEnvelope,
  pedidoSeguimientoEnvelope,
} from "../schemas/pedido.schema";
import {
  rutaConfirmacionPago,
  rutaPedido,
  rutaPreparacionPago,
} from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

export function usePedidoSeguimiento(token: string) {
  return useApiQuery({
    queryKey: marketplaceClaves.pedido(token),
    url: token ? rutaPedido(token) : null,
    schema: datosDelEnvelope(pedidoSeguimientoEnvelope),
    queryOptions: {
      enabled: Boolean(token),
      staleTime: STALE_TIME.comercial,
      gcTime: gcTimeFor(STALE_TIME.comercial),
    },
  });
}

export function usePagoPedido(token: string) {
  const preparar = useApiCreate<IzipayPreparacionPedido, void>({
    url: rutaPreparacionPago(token),
    schema: datosDelEnvelope(izipayPreparacionPedidoEnvelope),
    invalidateKeys: [marketplaceClaves.pedido(token)],
  });

  const confirmar = useApiCreate<
    PagoConfirmadoPedido,
    IzipayConfirmacionPedido
  >({
    url: rutaConfirmacionPago(token),
    schema: datosDelEnvelope(pagoConfirmadoPedidoEnvelope),
    invalidateKeys: [marketplaceClaves.pedido(token)],
  });

  return {
    prepararPago: preparar.mutateAsync,
    confirmarPago: confirmar.mutateAsync,
  };
}
