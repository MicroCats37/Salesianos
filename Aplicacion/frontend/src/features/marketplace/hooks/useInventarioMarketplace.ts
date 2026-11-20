"use client";

import { useApiCreate, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type {
  EntregaConfirmada,
  MovimientoInventario,
  MovimientoInventarioFormData,
} from "../schemas/inventario.schema";
import {
  entregaConfirmadaEnvelope,
  entregasEnvelope,
  inventarioEnvelope,
  movimientoInventarioEnvelope,
} from "../schemas/inventario.schema";
import {
  RUTA_ENTREGAS,
  RUTA_INVENTARIO,
  rutaConfirmarEntrega,
  rutaMovimientosInventario,
} from "../services/inventario.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

export function useInventarioMarketplace() {
  return useApiQuery({
    queryKey: marketplaceClaves.inventario(),
    url: RUTA_INVENTARIO,
    schema: datosDelEnvelope(inventarioEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.comercial,
      gcTime: gcTimeFor(STALE_TIME.comercial),
    },
  });
}

export function useRegistrarMovimientoInventario() {
  return useApiCreate<MovimientoInventario, MovimientoInventarioFormData>({
    url: rutaMovimientosInventario(),
    schema: datosDelEnvelope(movimientoInventarioEnvelope),
    invalidateKeys: [marketplaceClaves.todas],
  });
}

export function useEntregas() {
  return useApiQuery({
    queryKey: marketplaceClaves.entregas(),
    url: RUTA_ENTREGAS,
    schema: datosDelEnvelope(entregasEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.comercial,
      gcTime: gcTimeFor(STALE_TIME.comercial),
    },
  });
}

export function useConfirmarEntrega() {
  return useApiCreate<EntregaConfirmada, string>({
    url: (pedidoId) => rutaConfirmarEntrega(pedidoId),
    schema: datosDelEnvelope(entregaConfirmadaEnvelope),
    invalidateKeys: [marketplaceClaves.entregas()],
  });
}
