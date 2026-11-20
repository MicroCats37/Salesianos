"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { invalidarAdmin } from "@/features/admin/operaciones/utils/admin.cache.utils";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PayloadAprobarPagoManualAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import {
  aprobarPagoManualAdmin,
  listarPagosAdmin,
  obtenerPagoAdmin,
} from "../services/pago-admin.service";
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
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.pagos.listPage(
        parametrosListaAdminDesdeUrl(parametros),
      ),
      queryFn: () => listarPagosAdmin(parametrosListaAdminDesdeUrl(parametros)),
      kind: "listadoAdministrativo",
    }),
    enabled: RUTAS_ADMIN.pagosLista.registrado,
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.pagosLista.registrado,
    (pagina) => pagina.items,
  );
}

/** The commercial detail of a payment (`RT-PG-07`). */
export function useDetallePagoAdmin(
  compraId: string | undefined,
): EstadoDetallePagoAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.pagos.detail(compraId ?? ""),
      queryFn: () => obtenerPagoAdmin(compraId ?? ""),
      kind: "listadoAdministrativo",
    }),
    enabled: Boolean(compraId) && RUTAS_ADMIN.pagoDetalle.registrado,
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.pagoDetalle.registrado);
}

/**
 * The manual approval of a payment (the S-10 of `ADM-14`).
 *
 * The command is audited: it carries the reason and the amount that the
 * server published. The invalidation lives INSIDE the `mutationFn`
 * (`FND-08` §3 regla 5).
 *
 * The route does NOT exist: the command is rejected by the guard of the
 * service before the transport and the action stays DISABLED in the interface.
 */
export function useAprobarPagoManualAdmin() {
  const cliente = useQueryClient();

  return useMutation({
    mutationFn: async (payload: PayloadAprobarPagoManualAdmin) => {
      const resultado = await aprobarPagoManualAdmin(payload);

      await invalidarAdmin(cliente, "pagos");

      return resultado;
    },
  });
}
