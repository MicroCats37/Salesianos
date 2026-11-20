import { Store } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";

/**
 * SHOP-01 - the catalogue of the store.
 *
 * The store is a real surface of the edition: the merchandise of the
 * festival. The catalogue is published by the backend, so the grid waits
 * for it instead of showing placeholders that look like products.
 */
export function TiendaView() {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="SHOP-01"
        title="Tienda del festival"
        description="La merchandising de Salesianos FEST: cada producto tiene su precio y su stock, y la recogida se confirma en el punto del evento."
        tone="band"
      />

      <RouteEmptyState
        icon={Store}
        title="El catálogo todavía no está disponible"
        description="Los productos, sus precios y sus existencias los publica el servicio de la tienda. Esta rejilla se completará con esa fuente; no se muestran productos de ejemplo porque un precio inventado es una promesa que el servidor no puede cumplir."
      />
    </div>
  );
}
