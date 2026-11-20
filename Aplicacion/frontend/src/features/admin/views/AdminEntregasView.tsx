import { PackageCheck } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-20 - the pickups of the store.
 *
 * A purchase of the store is not finished when it is paid: it is finished
 * when the buyer picks it up. This route is the list of the pickups waiting
 * for a confirmation.
 */
export function AdminEntregasView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-20"
        title="Validar las recogidas"
        description="Los pedidos comprados que todavía no se han recogido, con la persona que debe retirarlos."
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

      <AdminPanel
        title="Recogidas por confirmar"
        description="Los pedidos pagados a la espera de que la persona los retire."
      >
        <AdminDataTable
          caption="Recogidas de la tienda por confirmar"
          columns={[
            { key: "pedido", label: "Pedido", identificador: true },
            { key: "persona", label: "Persona" },
            { key: "elementos", label: "Elementos", numerico: true },
            { key: "estado", label: "Estado" },
            { key: "fecha", label: "Fecha", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={PackageCheck}
              title="No hay recogidas pendientes"
              description="Las recogidas se leen del servicio de administración. Cuando la integración esté disponible, aquí se listarán los pedidos pagados a la espera de confirmación, con la persona que debe retirarlos."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
