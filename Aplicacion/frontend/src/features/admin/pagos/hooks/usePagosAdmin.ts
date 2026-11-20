"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import {
  RUTAS_ADMIN,
  urlDeRutaAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PayloadAprobarPagoManualAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import { useApiCreate } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import {
  adminPagoDetalleEnvelope,
  listaPagosAdminEnvelope,
  pagoAdminDetalleDesdeWire,
  pagoAdminItemEnvelope,
  pagoAdminListaDesdeWire,
} from "../schemas/pago-admin.schema";
import type {
  EstadoDetallePagoAdmin,
  EstadoPagosAdmin,
} from "../types/pagos-admin.types";

/**
 * The reads and the commands of the ADMINISTRATION OF THE PAYMENTS.
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the operational list (`ADM-14`) | `GET /administracion/pagos` (`RT-PG-04`) | `PaginatedData[AdminPagoListItemOut]` |
 * | the commercial detail | `GET /administracion/pagos/{compra_id}` (`RT-PG-07`) | `AdminPagoDetalleOut` |
 * | the manual approval | `POST /administracion/pagos/{orden_pago_id}/aprobar-manual` (`RT-PG-05`) | `AdminPagoAprobarManualOut` |
 *
 * ## The registration truth
 *
 * `AdminPagoController` is NOT registered: the three routes DO NOT EXIST,
 * even though `RT-PG-04` and `RT-PG-05` are FROZEN in GOV-01. The reads are
 * DISABLED and the surface shows the honest state.
 *
 * ## The verdict has ONE owner
 *
 * The `estado_operativo` of the row is the fact that the backend published.
 * The browser NEVER crosses the state of the purchase, the state of the order
 * and the messages of the provider to decide whether a payment is fine
 * (`GOV-02-RB-06a`).
 */

/** The operational list of the payments (`ADM-14`). */
export function useListaPagosAdmin(
  parametros: Record<string, string> | undefined,
): EstadoPagosAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.pagos.list,
    ruta: RUTAS_ADMIN.pagosLista,
    envelope: listaPagosAdminEnvelope,
    filtros: parametrosListaAdminDesdeUrl(parametros),
    select: (pagina) => pagina.items.map(pagoAdminListaDesdeWire),
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.pagosLista.registrado);
}

/** The commercial detail of a payment (`RT-PG-07`). */
export function useDetallePagoAdmin(
  compraId: string | undefined,
): EstadoDetallePagoAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.pagos.detail(compraId ?? ""),
    ruta: RUTAS_ADMIN.pagoDetalle,
    envelope: adminPagoDetalleEnvelope,
    parametros: compraId ? { compra_id: compraId } : undefined,
    enabled: Boolean(compraId),
    select: (detalle) => pagoAdminDetalleDesdeWire(detalle),
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.pagoDetalle.registrado);
}

/**
 * The manual approval of a payment (the S-10 of `ADM-14`).
 *
 * The command is audited: it carries the reason and the amount that the
 * server published. The invalidation lives INSIDE the mutation
 * (`FND-08` §3 regla 5).
 */
export function useAprobarPagoManualAdmin() {
  const mutacion = useApiCreate({
    getUrl: ({ id }) =>
      urlDeRutaAdmin(RUTAS_ADMIN.aprobarPagoManual, {
        orden_pago_id: String(id),
      }),
    schema: datosDelEnvelope(pagoAdminItemEnvelope),
    invalidateKeys: [adminClaves.pagos.all],
  });

  const separar = (args: PayloadAprobarPagoManualAdmin) => ({
    id: args.orden_pago_id,
    data: {
      canal: args.canal,
      referencia: args.referencia,
      motivo: args.motivo,
    },
  });

  return {
    ...mutacion,
    mutate: (
      args: PayloadAprobarPagoManualAdmin,
      options?: Parameters<typeof mutacion.mutate>[1],
    ) => mutacion.mutate(separar(args), options),
    mutateAsync: (args: PayloadAprobarPagoManualAdmin) =>
      mutacion.mutateAsync(separar(args)),
  };
}
