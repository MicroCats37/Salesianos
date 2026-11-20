"use client";

import { ImageOff, Package } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import type { ProductoListItem } from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";

export interface TarjetaProductoProps {
  /** The product of the catalogue. */
  producto: ProductoListItem;
  /**
   * The reason why the product cannot be bought.
   *
   * The stock is NOT part of the product wrapper (`DOM-04`): it belongs to
   * the inventory (`DOM-06`). The adapter resolves it and hands the reason
   * over, because a disabled control without a reason is a dead end.
   */
  motivoBloqueo?: string;
  /**
   * The currency of the price.
   *
   * The product wrapper of `DOM-04` does NOT declare a currency, so the
   * adapter hands it over when the edition publishes one. Without it the
   * amount is printed alone instead of guessing a currency.
   */
  moneda?: string;
  className?: string;
}

/**
 * TarjetaProducto - one product of the catalogue.
 *
 * The card shows the photos of the SERVER: when the file is missing or the
 * image fails, the well keeps its place and the alternative text of the
 * product survives (`RB-02` SHOP-01, "error de imagen").
 *
 * A product without stock is DISABLED with a written reason, never dimmed
 * only, and no action depends on hover.
 */
export function TarjetaProducto({
  producto,
  motivoBloqueo,
  moneda,
  className,
}: TarjetaProductoProps) {
  const [imagenRota, setImagenRota] = useState(false);
  const bloqueado = Boolean(motivoBloqueo);
  const url = producto.imagen_principal_url;
  const alt = producto.nombre;

  return (
    <article
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-3",
        className,
      )}
    >
      <div className="relative aspect-[4/3] overflow-hidden rounded-[var(--radius-md)] bg-surface-recessed">
        {url && !imagenRota ? (
          <img
            src={url}
            alt={alt}
            onError={() => setImagenRota(true)}
            className="size-full object-cover"
          />
        ) : (
          <span className="flex size-full flex-col items-center justify-center gap-1 text-muted-foreground">
            <ImageOff className="size-5" aria-hidden="true" />
            <span className="text-caption">{alt}</span>
          </span>
        )}
        {producto.oferta_activa ? (
          <span className="absolute top-2 left-2 rounded-full border border-success/45 bg-success/12 px-2.5 py-1 text-xs font-semibold text-foreground">
            Oferta
          </span>
        ) : null}
      </div>

      <div className="flex flex-col gap-1">
        <h3 className="text-base font-semibold text-foreground">
          {producto.nombre}
        </h3>
        {producto.categoria_nombre ? (
          <p className="text-caption text-muted-foreground">
            {producto.categoria_nombre}
          </p>
        ) : null}
        <p className="text-sm font-semibold tabular-nums text-foreground">
          {formatearMonto(producto.precio_efectivo, moneda ?? "")}
          {producto.oferta_activa && producto.precio_oferta !== null ? (
            <span className="ml-2 text-xs font-normal text-muted-foreground line-through">
              {formatearMonto(producto.precio, moneda ?? "")}
            </span>
          ) : null}
        </p>
      </div>

      {bloqueado ? (
        <p className="text-caption font-semibold text-destructive">
          {motivoBloqueo}
        </p>
      ) : null}

      <Button asChild variant="outline" className="min-h-11 w-full">
        <Link href={RUTAS.publico.tiendaProducto(producto.slug)}>
          <Package className="size-4" aria-hidden="true" />
          Ver el producto
        </Link>
      </Button>
    </article>
  );
}
