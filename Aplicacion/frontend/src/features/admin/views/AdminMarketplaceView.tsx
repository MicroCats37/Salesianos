"use client";

import { ExternalLink, Package, Plus, Store } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import {
  useCatalogoTienda,
  useCategoriasTienda,
  useCrearProducto,
} from "@/features/marketplace/hooks/useCatalogoTienda";
import {
  useInventarioMarketplace,
  useRegistrarMovimientoInventario,
} from "@/features/marketplace/hooks/useInventarioMarketplace";
import { RUTAS } from "@/lib/routes";
import { resolveImageUrl } from "@/lib/utils";
import { AdminProductoCrearModal } from "../marketplace/components/AdminProductoCrearModal";
import { AdminEntregasView } from "./AdminEntregasView";

/**
 * ADM-17 - the store of the edition.
 *
 * The operational index of the published catalogue, its inventory summary,
 * and the pending physical handovers.
 */
export function AdminMarketplaceView() {
  const [modalAbierto, setModalAbierto] = useState(false);
  const catalogo = useCatalogoTienda({ page: 1, page_size: 100 });
  const categorias = useCategoriasTienda();
  const crearProducto = useCrearProducto();
  const inventario = useInventarioMarketplace();
  const registrarMovimiento = useRegistrarMovimientoInventario();
  const stockPorProducto = new Map(
    (inventario.data ?? []).map((item) => [item.producto_id, item.stock]),
  );

  const nuevoProducto = (
    <Button
      type="button"
      className="min-h-11"
      onClick={() => setModalAbierto(true)}
    >
      <Plus className="size-4" aria-hidden="true" />
      Nuevo producto
    </Button>
  );

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-17"
        title="Gestionar productos"
        description="Consulta el catálogo publicado, su precio vigente, oferta, stock y disponibilidad."
        actions={nuevoProducto}
      />

      <AdminSubnav
        ariaLabel="Secciones de la tienda"
        items={[
          {
            href: RUTAS.administracion.marketplace,
            label: "Tienda",
            description: "Catálogo y precios",
          },
          {
            href: RUTAS.administracion.marketplaceInventario,
            label: "Inventario",
            description: "Movimientos de stock",
          },
        ]}
      />

      <AdminPanel
        title="Productos"
        description="Una vista operativa del catálogo. El backend decide precios, ofertas y disponibilidad."
        actions={nuevoProducto}
      >
        {catalogo.isPending ? (
          <output className="block py-10 text-center text-sm text-muted-foreground">
            Cargando productos de la tienda...
          </output>
        ) : null}
        {catalogo.isError ? (
          <div
            role="alert"
            className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"
          >
            No pudimos cargar los productos de la tienda. Inténtalo de nuevo en
            unos segundos.
          </div>
        ) : null}
        {catalogo.isSuccess ? (
          <AdminDataTable
            caption="Productos del catálogo de la tienda"
            columns={[
              { key: "producto", label: "Producto" },
              { key: "categoria", label: "Categoría" },
              { key: "precio", label: "Precio vigente", numerico: true },
              { key: "oferta", label: "Oferta" },
              { key: "stock", label: "Stock", numerico: true },
              { key: "estado", label: "Estado" },
              { key: "acciones", label: "Acciones" },
            ]}
            filas={catalogo.data.items.map((producto) => ({
              cells: {
                producto: (
                  <div className="flex min-w-48 items-center gap-3">
                    {producto.imagen_principal_url ? (
                      <img
                        src={resolveImageUrl(producto.imagen_principal_url)}
                        alt=""
                        className="size-10 rounded-[var(--radius-sm)] object-cover"
                      />
                    ) : (
                      <span className="flex size-10 items-center justify-center rounded-[var(--radius-sm)] bg-surface-recessed text-muted-foreground">
                        <Package className="size-4" aria-hidden="true" />
                      </span>
                    )}
                    <div className="min-w-0">
                      <p className="truncate font-medium text-foreground">
                        {producto.nombre}
                      </p>
                      <p className="text-caption text-muted-foreground">
                        {producto.cantidad_imagenes} imágenes
                      </p>
                    </div>
                  </div>
                ),
                categoria: producto.categoria_nombre ?? "Sin categoría",
                precio: new Intl.NumberFormat("es-ES", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }).format(producto.precio_efectivo),
                oferta: producto.oferta_activa ? "Vigente" : "Sin oferta",
                stock: stockPorProducto.get(producto.id) ?? 0,
                estado: producto.estado === "ACTIVO" ? "Activo" : "Inactivo",
                acciones: (
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="min-h-9 whitespace-nowrap"
                  >
                    <Link
                      href={RUTAS.administracion.marketplaceProducto(
                        producto.slug,
                      )}
                    >
                      Ver detalle
                      <ExternalLink className="size-3.5" aria-hidden="true" />
                    </Link>
                  </Button>
                ),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={Store}
                title="Todavía no hay productos cargados"
                description="Crea el primer producto para publicarlo en el catálogo de la tienda."
                action={nuevoProducto}
              />
            }
          />
        ) : null}
      </AdminPanel>

      <AdminEntregasView embedded />

      {modalAbierto ? (
        <AdminProductoCrearModal
          open={modalAbierto}
          onOpenChange={setModalAbierto}
          categorias={categorias.data ?? []}
          categoriasCargando={categorias.isPending}
          creando={crearProducto.isPending || registrarMovimiento.isPending}
          onCrear={async (datos) => {
            const producto = await crearProducto.mutateAsync(datos);
            if (datos.stock_inicial > 0) {
              await registrarMovimiento.mutateAsync({
                producto_id: producto.id,
                tipo: "REPOSICION",
                cantidad: datos.stock_inicial,
                motivo: "Stock inicial al crear el producto.",
              });
            }
            await catalogo.refetch();
          }}
        />
      ) : null}
    </div>
  );
}
