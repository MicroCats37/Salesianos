import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PayloadAprobarPagoManualAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import {
  adminPagoDetalleEnvelope,
  listaPagosAdminEnvelope,
  pagoAdminDetalleDesdeWire,
  pagoAdminItemEnvelope,
  pagoAdminListaDesdeWire,
} from "../schemas/pago-admin.schema";
import type {
  AdminPagoDetalleOut,
  AdminPagoListItemOut,
} from "../types/pagos-admin.types";

/**
 * The client of the ADMINISTRATION OF THE PAYMENTS.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-PG-04` | GET | `/administracion/pagos` | `PaginatedData[AdminPagoListItemOut]` |
 * | `RT-PG-07` | GET | `/administracion/pagos/{compra_id}` | `AdminPagoDetalleOut` |
 * | `RT-PG-05` | POST | `/administracion/pagos/{orden_pago_id}/aprobar-manual` | `AdminPagoAprobarManualOut` |
 *
 * ## The registration truth
 *
 * `AdminPagoController` is NOT registered in
 * `Aplicacion/backend/config/api.py`: the three routes DO NOT EXIST, even
 * though `RT-PG-04` and `RT-PG-05` are FROZEN in GOV-01. The guard of
 * `pedirAdmin` REJECTS them before the transport (`A0-API04-05`).
 *
 * ## The verdict has ONE owner
 *
 * The `estado_operativo` of the row is the fact that the backend published.
 * The browser NEVER crosses the state of the purchase, the state of the order
 * and the messages of the provider to decide whether a payment is fine
 * (`GOV-02-RB-06a` · `contratos/01` §1.4).
 *
 * ## The manual approval
 *
 * The command is audited: it carries the reason and it never carries the
 * amount CALCULATED by the browser (the amount is the one the server
 * published). The wrapper `AdminPagoAprobarManualOut` is not published by the
 * backend yet: the answer is read with the mirror of the operational payment
 * and the reconciliation is an A0 request (`A0-API04-01`).
 */

/** The operational list of the payments (`RT-PG-04`). */
export async function listarPagosAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<AdminPagoListItemOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.pagosLista,
    listaPagosAdminEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return {
    ...pagina,
    items: pagina.items.map(pagoAdminListaDesdeWire),
  };
}

/** The commercial detail of a payment (`RT-PG-07`). */
export async function obtenerPagoAdmin(
  compraId: string,
): Promise<AdminPagoDetalleOut> {
  const detalle = await pedirAdmin(RUTAS_ADMIN.pagoDetalle, adminPagoDetalleEnvelope, {
    pathParams: { compra_id: compraId },
  });

  return pagoAdminDetalleDesdeWire(detalle);
}

/**
 * The manual approval of a payment (`RT-PG-05`).
 *
 * The command carries the audited reason. The amount is the one the server
 * published: the browser NEVER computes it and NEVER sends a price it
 * invented (`FR-08` §2.4).
 */
export async function aprobarPagoManualAdmin(
  payload: PayloadAprobarPagoManualAdmin,
): Promise<AdminPagoListItemOut> {
  const respuesta = await pedirAdmin(
    RUTAS_ADMIN.aprobarPagoManual,
    pagoAdminItemEnvelope,
    {
      pathParams: { orden_pago_id: payload.orden_pago_id },
      payload: {
        monto: payload.monto,
        moneda: payload.moneda,
        motivo: payload.motivo,
        ...(payload.version === undefined ? {} : { version: payload.version }),
      },
    },
  );

  return pagoAdminListaDesdeWire(respuesta);
}
