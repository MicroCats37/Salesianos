import { Package } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-18 - the editor of a product.
 *
 * A product is three things that must stay together: the images that sell
 * it, the offer that prices it and the stock that promises it.
 */
export function AdminProductoDetalleView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-18"
        title="Editar la galería y la oferta de un producto"
        description="La ficha completa de un producto del catálogo: sus imágenes, su precio, su categoría y su disponibilidad."
        meta={[{ etiqueta: "Producto", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.marketplace}>
              Volver a la tienda
            </Link>
          </Button>
        }
      />

      <AdminPanel
        title="Galería"
        description="Las imágenes del producto y su orden de publicación."
      >
        <AdminEmptyState
          icon={Package}
          title="Todavía no hay imágenes cargadas"
          description="La galería se lee del servicio de administración. Cuando la integración esté disponible, aquí se verán las imágenes del producto con su orden y con la acción de quitarlas."
        />
      </AdminPanel>

      <AdminPanel
        title="Oferta"
        description="Precio, categoría, disponibilidad y estado de publicación del producto."
      >
        <AdminDataTable
          caption="Datos de la oferta del producto"
          columns={[
            { key: "campo", label: "Dato" },
            { key: "valor", label: "Valor" },
          ]}
          vacio={
            <AdminEmptyState
              icon={Package}
              title="Todavía no hay oferta cargada"
              description="El precio y la disponibilidad del producto los fija el backend: el formulario se los pedirá al servidor y nunca los escribirá por su cuenta."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
