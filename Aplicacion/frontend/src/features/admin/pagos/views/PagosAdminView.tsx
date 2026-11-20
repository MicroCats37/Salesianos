import { CreditCard } from "lucide-react";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import {
  BarraFiltros,
  BusquedaOperativa,
  CODIGOS_ESTADO_OPERATIVO_PAGO,
  EsqueletoOperativo,
  MarcoOperativo,
} from "@/features/admin/operaciones";
import type { ColumnaOperativa, FiltroOperativo } from "@/features/admin/operaciones";
import { ListaPagosOperativa } from "../components/ListaPagosOperativa";
import type {
  AdminPagoDetalleOut,
  EstadoPagosAdmin,
} from "../types/pagos-admin.types";

const COLUMNAS: ColumnaOperativa[] = [
  { key: "compra", label: "Compra", prioridad: 1, titular: true, identificador: true },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "total", label: "Total", prioridad: 1, numerico: true },
  { key: "concepto", label: "Concepto", prioridad: 2 },
  { key: "comprador", label: "Comprador", prioridad: 2 },
  { key: "tipo", label: "Tipo", prioridad: 2 },
  { key: "fecha", label: "Fecha", prioridad: 2 },
  { key: "accion", label: "Acción", prioridad: 2 },
];

/**
 * The filters of the operational list.
 *
 * `estado_operativo` is a FROZEN OBLIGATION of this route (`RT-PG-04` ·
 * `GOV-02-RB-06b`): the backend already accepts the filter and the interface
 * has to expose it.
 *
 * Every vocabulary below is the REAL one of the target backend:
 * `EstadoOperativoPago` (`pagos`), `OrigenCompra` (`commerce`),
 * `EstadoCompra` (`commerce`) and `EstadoOrdenPago` (`pagos`).
 */
const FILTROS: FiltroOperativo[] = [
  {
    clave: "estado_operativo",
    etiqueta: "Estado operativo",
    opciones: CODIGOS_ESTADO_OPERATIVO_PAGO.map((codigo) => ({
      valor: codigo.codigo,
      etiqueta: codigo.etiqueta,
    })),
  },
  {
    clave: "tipo",
    etiqueta: "Tipo de compra",
    opciones: [
      { valor: "INSCRIPCION", etiqueta: "Inscripción" },
      { valor: "PASE", etiqueta: "Pase" },
      { valor: "MARKETPLACE", etiqueta: "Marketplace" },
    ],
  },
  {
    clave: "estado_compra",
    etiqueta: "Estado de la compra",
    opciones: [
      { valor: "PENDIENTE", etiqueta: "Pendiente" },
      { valor: "PAGADA", etiqueta: "Pagada" },
      { valor: "CANCELADA", etiqueta: "Cancelada" },
    ],
  },
  {
    clave: "estado_orden",
    etiqueta: "Estado de la orden",
    opciones: [
      { valor: "PENDIENTE", etiqueta: "Pendiente" },
      { valor: "EN_VERIFICACION", etiqueta: "En verificación" },
      { valor: "CONFIRMADA", etiqueta: "Confirmada" },
      { valor: "FALLIDA", etiqueta: "Fallida" },
      { valor: "VENCIDA", etiqueta: "Vencida" },
    ],
  },
  { clave: "desde", etiqueta: "Desde", opciones: [], tipo: "fecha" },
  { clave: "hasta", etiqueta: "Hasta", opciones: [], tipo: "fecha" },
];

export interface PagosAdminViewProps {
  /** The state of the list. The default is the honest one. */
  estado?: EstadoPagosAdmin;
  /** EVERY query parameter of the current URL. */
  parametros?: Record<string, string>;
  /** The commercial detail of each purchase, when it arrived. */
  detalles?: Readonly<Record<string, AdminPagoDetalleOut>>;
}

/**
 * ADM-14 - `/administracion/pagos`.
 *
 * The route separates THREE levels (`frontend/04` §6):
 *
 * 1. the operational list — one understandable state per row;
 * 2. the commercial detail — what was bought, the state of the payment, what
 *    was obtained and the next permitted action;
 * 3. the diagnosis and audit — the order, the attempts of the provider, the
 *    evidence and the manual operations, HIDDEN BY DEFAULT.
 *
 * The browser NEVER crosses the state of the purchase, the state of the
 * order and the messages of the provider to decide whether a payment is
 * fine: the presenter publishes the verdict and this route reproduces it
 * (`GOV-02-RB-06a`).
 */
export function PagosAdminView({
  estado = { estado: "sin-datos" },
  parametros = {},
  detalles,
}: PagosAdminViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-14"
        title="Investigar compras, órdenes y pagos"
        description="Las compras de la edición con el veredicto operativo de su pago: cuántas están pagadas, cuántas pendientes y qué monto falta por cobrar."
      />

      <AdminNotice title="Acciones sensibles, nivel de break-glass">
        Registrar un pago manual, anular una aprobación y cancelar una
        compra de pases exigen un motivo auditado y la capacidad de
        aprobación de pagos. El personal de staff lee esta lista; el personal
        con capacidad de aprobación ve además los botones.
      </AdminNotice>

      <BusquedaOperativa
        parametros={parametros}
        etiqueta="Buscar compra"
        placeholder="Compra, orden, comprador o concepto"
      />

      <BarraFiltros
        filtros={FILTROS}
        parametros={parametros}
        etiqueta="Filtros de los pagos"
      />

      <AdminPanel
        title="Compras y órdenes"
        description="Una fila por compra, con su responsable, su tipo y el veredicto del pago."
      >
        <MarcoOperativo
          estado={estado}
          sinDatos={
            <AdminEmptyState
              icon={CreditCard}
              title="Todavía no hay compras cargadas"
              description="Las compras y sus órdenes se leen del servicio de administración, que todavía no expone su ruta. Cuando exista, aquí se listarán con su veredicto de pago y su evidencia, con los filtros por estado, por tipo y por rango de fechas."
            />
          }
          cargando={<EsqueletoOperativo columnas={COLUMNAS} />}
        >
          {(datos) => (
            <ListaPagosOperativa
              pagos={datos}
              detalles={detalles}
              filtroVeredicto={parametros.estado_operativo}
            />
          )}
        </MarcoOperativo>
      </AdminPanel>
    </div>
  );
}
