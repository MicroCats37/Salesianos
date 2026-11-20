"use client";

import { handleApiError } from "@/errors";
import { TarjetaProducto } from "@/features/marketplace/components/TarjetaProducto";
import { useCatalogoTienda } from "@/features/marketplace/hooks/useCatalogoTienda";
import { PortadaSection } from "./PortadaSection";

/** A preview of the published store catalogue on the festival landing page. */
export function TiendaSection() {
  const productos = useCatalogoTienda({ page: 1, page_size: 100 });
  const error = productos.error ? handleApiError(productos.error) : null;
  const destacados = productos.data?.items ?? [];

  return (
    <PortadaSection
      id="tienda"
      eyebrow="TIENDA / SALESIANOS FEST"
      titulo={["LLEVA EL", "FESTIVAL", "CONTIGO."]}
      destacado="CONTIGO."
      copy="Descubre los productos oficiales publicados para esta edición. Los precios y la disponibilidad siempre vienen del catálogo del festival."
    >
      <div className="mt-10" data-portada-stagger>
        {productos.isPending ? (
          <p className="text-sm text-muted-foreground">
            Cargando productos oficiales...
          </p>
        ) : null}

        {error ? (
          <p className="text-sm text-destructive">{error.message}</p>
        ) : null}

        {!productos.isPending && !error && destacados.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            La tienda todavía no tiene productos publicados para esta edición.
          </p>
        ) : null}

        {destacados.length > 0 ? (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {destacados.map((producto) => (
              <li key={producto.id}>
                <TarjetaProducto producto={producto} />
              </li>
            ))}
          </ul>
        ) : null}

      </div>
    </PortadaSection>
  );
}
