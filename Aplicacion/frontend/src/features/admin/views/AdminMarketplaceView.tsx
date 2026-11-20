import { Store } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-17 - the store of the edition.
 *
 * The store has two faces: the catalogue that is published and the orders
 * that come in. They live in the same route but not in the same table, so
 * they are two blocks side by side instead of one list with two meanings.
 */
export function AdminMarketplaceView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-17"
        title="Gestionar la tienda: productos y pedidos"
        description="El catálogo que la edición publica y los pedidos que entran por él, con su estado y su importe."
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
        title="Productos"
        description="El catálogo publicado en la tienda, con su categoría, su precio y su estado."
      >
        <AdminDataTable
          caption="Productos del catálogo de la tienda"
          columns={[
            { key: "producto", label: "Producto" },
            { key: "categoria", label: "Categoría" },
            { key: "precio", label: "Precio", numerico: true },
            { key: "estado", label: "Estado" },
          ]}
          vacio={
            <AdminEmptyState
              icon={Store}
              title="Todavía no hay productos cargados"
              description="El catálogo de la tienda se lee del servicio de administración. Cuando la integración esté disponible, aquí se listarán los productos con su categoría, su precio y su estado."
            />
          }
        />
      </AdminPanel>

      <AdminPanel
        title="Pedidos"
        description="Los pedidos recibidos, con su comprador, su importe y su estado."
      >
        <AdminDataTable
          caption="Pedidos de la tienda"
          columns={[
            { key: "pedido", label: "Pedido", identificador: true },
            { key: "comprador", label: "Comprador" },
            { key: "total", label: "Total", numerico: true },
            { key: "estado", label: "Estado" },
            { key: "fecha", label: "Fecha", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={Store}
              title="Todavía no hay pedidos cargados"
              description="Los pedidos se leen del servicio de administración, con su estado de preparación y su aviso de recogida."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
