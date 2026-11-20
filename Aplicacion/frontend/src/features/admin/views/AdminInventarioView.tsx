import { Boxes } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-19 - the stock movements of the store.
 *
 * Stock is not a number that is edited: it is the sum of the movements.
 * The route shows the movements, and the movements are the record.
 */
export function AdminInventarioView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-19"
        title="Registrar movimientos de stock"
        description="Las entradas y las salidas de existencias de la tienda, con su motivo y su fecha."
      />

      <AdminSubnav
        ariaLabel="Secciones de la tienda"
        items={[
          {
            href: RUTAS.administracion.marketplace,
            label: "Tienda",
            description: "Productos y pedidos",
          },
          {
            href: RUTAS.administracion.marketplaceInventario,
            label: "Inventario",
            description: "Movimientos de stock",
          },
          {
            href: RUTAS.administracion.marketplaceEntregas,
            label: "Entregas",
            description: "Recogidas por confirmar",
          },
        ]}
      />

      <AdminNotice title="Las existencias son la suma de los movimientos">
        Esta pantalla no edita una cifra de stock: registra los movimientos
        que la componen. El saldo que se vea en el producto es el que
        calcula el backend.
      </AdminNotice>

      <AdminPanel
        title="Movimientos"
        description="Las entradas y salidas de existencias, con su cantidad y su motivo."
      >
        <AdminDataTable
          caption="Movimientos de stock de la tienda"
          columns={[
            { key: "producto", label: "Producto" },
            { key: "referencia", label: "Referencia", identificador: true },
            { key: "cantidad", label: "Cantidad", numerico: true },
            { key: "tipo", label: "Tipo" },
            { key: "fecha", label: "Fecha", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={Boxes}
              title="Todavía no hay movimientos de stock"
              description="Los movimientos se leen del servicio de administración. Cuando la integración esté disponible, aquí se listarán con su tipo y su motivo, y el alta se habilitará sobre la misma lista."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
