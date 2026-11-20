"use client";

import { Package } from "lucide-react";
import Link from "next/link";
import {
  ShellErrorState,
  ShellPendingState,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { useProductoDetalle } from "@/features/marketplace/hooks/useProductoDetalle";
import { RUTAS } from "@/lib/routes";
import { resolveImageUrl } from "@/lib/utils";

const formatoMoneda = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
});

/** ADM-18 - the real read-only product detail published by the marketplace. */
export function AdminProductoDetalleView({ id: slug }: { id: string }) {
  const producto = useProductoDetalle(slug);

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-18"
        title={producto.data?.nombre ?? "Detalle de producto"}
        description="Consulta la ficha comercial, el precio vigente y la galería publicada por el servidor."
        meta={[{ etiqueta: "Referencia", valor: slug }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.marketplace}>
              Volver a productos
            </Link>
          </Button>
        }
      />

      {producto.isPending ? (
        <ShellPendingState
          title="Cargando el producto"
          description="Estamos leyendo su ficha y galería."
        />
      ) : null}
      {producto.isError ? (
        <ShellErrorState
          title="No pudimos cargar este producto"
          description={producto.error.message}
          accion={{ label: "Reintentar", onClick: () => producto.refetch() }}
        />
      ) : null}
      {producto.isSuccess ? (
        <>
          <AdminPanel
            title="Oferta"
            description="Importes y estado publicados por el backend."
          >
            <AdminDataTable
              caption="Datos comerciales del producto"
              columns={[
                { key: "dato", label: "Dato" },
                { key: "valor", label: "Valor" },
              ]}
              filas={[
                {
                  cells: {
                    dato: "Categoría",
                    valor: producto.data.categoria_nombre ?? "Sin categoría",
                  },
                },
                {
                  cells: {
                    dato: "Precio regular",
                    valor: formatoMoneda.format(producto.data.precio),
                  },
                },
                {
                  cells: {
                    dato: "Precio vigente",
                    valor: formatoMoneda.format(producto.data.precio_efectivo),
                  },
                },
                {
                  cells: {
                    dato: "Oferta",
                    valor: producto.data.oferta_activa
                      ? "Vigente"
                      : "Sin oferta vigente",
                  },
                },
                {
                  cells: {
                    dato: "Estado",
                    valor:
                      producto.data.estado === "ACTIVO" ? "Activo" : "Inactivo",
                  },
                },
              ]}
            />
          </AdminPanel>

          <AdminPanel
            title="Galería"
            description="Imágenes publicadas para este producto."
          >
            {producto.data.imagenes.length > 0 ? (
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {producto.data.imagenes.map((imagen) => (
                  <li
                    key={imagen.id}
                    className="overflow-hidden rounded-[var(--radius-md)] border border-border bg-surface-recessed"
                  >
                    {imagen.url && imagen.disponible ? (
                      <img
                        src={resolveImageUrl(imagen.url)}
                        alt={imagen.texto_alternativo}
                        className="aspect-square w-full object-cover"
                      />
                    ) : (
                      <div className="flex aspect-square items-center justify-center text-sm text-muted-foreground">
                        Imagen no disponible
                      </div>
                    )}
                    <p className="p-3 text-sm text-muted-foreground">
                      {imagen.texto_alternativo || "Imagen de producto"}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <AdminEmptyState
                icon={Package}
                title="Este producto no tiene imágenes"
                description="La ficha está publicada, pero todavía no se cargó una imagen para su galería."
              />
            )}
          </AdminPanel>
        </>
      ) : null}
    </div>
  );
}
