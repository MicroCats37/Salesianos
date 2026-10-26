"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminPagoDetalleEnvelope,
  AdminPagoListadoEnvelope,
} from "../schemas";
import {
  getAdminPagoDetalle,
  getAdminPagos,
} from "../services/admin.pago.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/** Page of the payments table (A5). */
export const adminPagosQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminPagoListadoEnvelope,
    ApiQueryError,
    AdminPagoListadoEnvelope,
    readonly ["admin", "pagos", Record<string, string | number>]
  >({
    queryKey: ["admin", "pagos", adminParametrosConsulta(estado)],
    queryFn: () => getAdminPagos(estado),
    staleTime: 30 * 1000,
  });

/** Drilldown of one payment order (A6). */
export const adminPagoDetalleQueryOptions = (ordenPagoId: string) =>
  queryOptions<
    AdminPagoDetalleEnvelope,
    ApiQueryError,
    AdminPagoDetalleEnvelope,
    readonly ["admin", "pago", string]
  >({
    queryKey: ["admin", "pago", ordenPagoId],
    queryFn: () => getAdminPagoDetalle(ordenPagoId),
    enabled: Boolean(ordenPagoId),
    staleTime: 30 * 1000,
  });

export function useAdminPagos(estado: AdminEstadoLista) {
  return useQuery(adminPagosQueryOptions(estado));
}

export function useAdminPagoDetalle(ordenPagoId: string) {
  return useQuery(adminPagoDetalleQueryOptions(ordenPagoId));
}
