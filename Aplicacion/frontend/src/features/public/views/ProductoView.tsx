import { ArrowLeft, Package } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { RUTAS } from "@/lib/routes";

/**
 * SHOP-02 - the detail of a product and the creation of its order.
 *
 * The slug is the identity of the product in the URL. The page shows what
 * the server publishes about it: its price, its availability and its
 * gallery. It never invents a price to be able to offer a "buy" button.
 */
export function ProductoView({ slug }: { slug: string }) {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="SHOP-02"
        title="Producto del catálogo"
        description="La ficha del producto con su galería, su precio vigente y sus existencias, y el pedido a partir de ella."
        facts={[{ label: "Referencia", value: slug }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.publico.tienda}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a la tienda
            </Link>
          </Button>
        }
      />

      <RouteEmptyState
        icon={Package}
        title="Este producto todavía no se puede mostrar"
        description="La ficha del producto la publica el servicio de la tienda con su precio y su stock. Cuando el servicio esté conectado, aquí se verán sus imágenes y el pedido se podrá crear desde esta misma pantalla."
      />
    </div>
  );
}
