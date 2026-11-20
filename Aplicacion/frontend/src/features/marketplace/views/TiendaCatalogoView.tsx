import { Store } from "lucide-react";
import Link from "next/link";
import { FestivalPublicPage } from "@/components/shell/FestivalPublicPage";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { TarjetaProducto } from "../components/TarjetaProducto";
import type {
  CategoriaProducto,
  EstadoVistaTienda,
  ProductoListItem,
} from "../types/marketplace.types";

export interface TiendaCatalogoViewProps {
  /** The state of the catalogue. */
  estado?: EstadoVistaTienda;
  /** The products of the catalogue. */
  productos?: ProductoListItem[];
  /** The categories of the catalogue. */
  categorias?: CategoriaProducto[];
  /** The category that is active, read from the URL by the page. */
  categoriaActiva?: string;
  /** The currency of the price, when the edition publishes one. */
  moneda?: string;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the
   * server chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}

/**
 * SHOP-01 - the catalogue of the store.
 *
 * The store is a real surface of the edition: the merchandise of the
 * festival. The catalogue is published by the backend, so the grid waits for
 * it instead of showing placeholders that look like products.
 *
 * The filter of the category lives in the URL (`RB-02` SHOP-01): the page
 * reads it and the service filters. The browser never filters a catalogue on
 * its own.
 */
export function TiendaCatalogoView({
  estado = "sin-datos",
  productos = [],
  categorias = [],
  categoriaActiva,
  moneda,
  mensajeError,
  reintentar,
}: TiendaCatalogoViewProps) {
  const sinProductos = estado === "listo" && productos.length === 0;
  const filtrado = Boolean(categoriaActiva);

  return (
    <FestivalPublicPage
      eyebrow="TIENDA / SALESIANOS FEST"
      title={["LLEVA EL", "FESTIVAL", "CONTIGO."]}
      highlighted="CONTIGO."
      description="Productos oficiales para recordar el encuentro. Cada precio, existencia y entrega los confirma la organización."
    >
      {estado === "sin-permiso" ? (
        <ShellPermissionDenied
          title="No podemos mostrarte la tienda"
          description="Esta zona del festival no está disponible para ti ahora mismo."
          className="border-border bg-surface-raised"
        />
      ) : null}

      {estado === "cargando" ? (
        <ShellPendingState
          title="Cargando el catálogo de la tienda"
          description="Estamos leyendo los productos publicados en esta edición."
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar el catálogo de la tienda"
          description={
            mensajeError ??
            "No pudimos leer los productos en este momento. Vuelve a intentarlo en unos segundos."
          }
          accion={
            reintentar
              ? { label: "Reintentar", onClick: reintentar }
              : undefined
          }
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={Store}
          title="El catálogo de la tienda todavía no está disponible"
          description="Los productos, sus precios y sus existencias los publica el servicio de la tienda. Esta rejilla se completará con esa fuente; no se muestran productos de ejemplo porque un precio inventado es una promesa que el servidor no puede cumplir."
        />
      ) : null}

      {sinProductos && !filtrado ? (
        <RouteEmptyState
          icon={Store}
          title="No hay productos publicados en esta edición"
          description="La tienda de esta edición todavía no publica productos. Vuelve más tarde o mira el programa del festival."
        />
      ) : null}

      {sinProductos && filtrado ? (
        <RouteEmptyState
          icon={Store}
          title="No hay productos en esta categoría"
          description="La categoría activa no tiene productos publicados. Quita el filtro para ver el catálogo completo."
          action={
            <Link
              href={RUTAS.publico.tienda}
              className="text-sm font-semibold text-primary underline-offset-4 hover:underline"
            >
              Quitar el filtro
            </Link>
          }
        />
      ) : null}

      {categorias.length > 0 ? (
        <nav
          aria-label="Categorías de la tienda"
          className="flex flex-wrap gap-2"
        >
          {categorias.map((categoria) => (
            <Link
              key={categoria.id}
              href={`${RUTAS.publico.tienda}?categoria=${categoria.slug}`}
              aria-current={
                categoriaActiva === categoria.slug ? "true" : undefined
              }
              className={cn(
                "inline-flex min-h-11 items-center rounded-full border px-3 text-sm",
                categoriaActiva === categoria.slug
                  ? "border-primary bg-surface-raised font-semibold text-foreground"
                  : "border-border text-muted-foreground",
              )}
            >
              {categoria.nombre}
            </Link>
          ))}
        </nav>
      ) : null}

      {estado === "listo" && productos.length > 0 ? (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {productos.map((producto) => (
            <li key={producto.id}>
              <TarjetaProducto producto={producto} moneda={moneda} />
            </li>
          ))}
        </ul>
      ) : null}
    </FestivalPublicPage>
  );
}
