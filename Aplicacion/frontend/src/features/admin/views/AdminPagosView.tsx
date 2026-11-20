import { CreditCard } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-14 - the purchases, the orders and the payments.
 *
 * The table shows ONE state per row: the operational verdict of the
 * operator. The three facts that compose it —the state of the purchase, the
 * state of the order and the date of payment— stay in the drilldown as an
 * audit trail. The browser never recalculates the verdict.
 */
export function AdminPagosView() {
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

      <AdminPanel
        title="Compras y órdenes"
        description="Una fila por orden, con su responsable, su tipo y el veredicto del pago."
      >
        <AdminDataTable
          caption="Compras, órdenes de pago y su veredicto"
          columns={[
            { key: "orden", label: "N.º de orden", identificador: true },
            { key: "responsable", label: "Responsable" },
            { key: "tipo", label: "Tipo" },
            { key: "producto", label: "Producto" },
            { key: "cantidad", label: "Cantidad", numerico: true },
            { key: "total", label: "Total", numerico: true },
            { key: "estado", label: "Estado del pago" },
            { key: "pagada", label: "Pagada el", numerico: true },
            { key: "creada", label: "Creada", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={CreditCard}
              title="Todavía no hay compras cargadas"
              description="Las compras y sus órdenes se leen del servicio de administración. Cuando la integración esté disponible, aquí se listarán con su veredicto de pago y su evidencia, con los filtros por tipo, por estado y por rango de fechas."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
