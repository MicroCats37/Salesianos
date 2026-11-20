"use client";

import { ChevronLeft, ChevronRight, ImageOff } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn, resolveImageUrl } from "@/lib/utils";
import type { ImagenProducto } from "../types/marketplace.types";

export interface GaleriaProductoProps {
  /** The ordered gallery of the product. */
  imagenes: ImagenProducto[];
  className?: string;
}

/**
 * GaleriaProducto - the ordered gallery of a product.
 *
 * The order of the array IS the canonical order of the images (`FR-06` 2.4).
 *
 * The gallery is composed with the local `button` primitive instead of the
 * registry `carousel`: the local carousel ships English screen-reader labels
 * ("Previous slide") and `components/ui/**` is a forbidden root. See the
 * shadcn comparison of the evidence file.
 */
export function GaleriaProducto({ imagenes, className }: GaleriaProductoProps) {
  const [indice, setIndice] = useState(0);
  const total = imagenes.length;
  const actual = imagenes[indice];

  if (!actual) {
    return (
      <div
        className={cn(
          "flex aspect-[4/3] items-center justify-center rounded-[var(--radius-lg)] bg-surface-recessed text-muted-foreground",
          className,
        )}
      >
        <span className="flex flex-col items-center gap-1">
          <ImageOff className="size-5" aria-hidden="true" />
          <span className="text-caption">Este producto no tiene imagen</span>
        </span>
      </div>
    );
  }

  const sinArchivo = actual.url === null || !actual.disponible;

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="relative aspect-[4/3] overflow-hidden rounded-[var(--radius-lg)] bg-surface-recessed">
        {sinArchivo ? (
          <span className="flex size-full flex-col items-center justify-center gap-1 text-muted-foreground">
            <ImageOff className="size-5" aria-hidden="true" />
            <span className="text-caption">{actual.texto_alternativo}</span>
          </span>
        ) : (
          <img
            src={resolveImageUrl(actual.url)}
            alt={actual.texto_alternativo}
            className="size-full object-cover"
          />
        )}
      </div>

      <div className="flex items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="min-h-11 min-w-11"
          onClick={() => setIndice(Math.max(0, indice - 1))}
          disabled={indice === 0}
          aria-label="Imagen anterior"
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
        </Button>

        <p aria-live="polite" className="text-caption text-muted-foreground">
          {`Imagen ${indice + 1} de ${total}`}
        </p>

        <Button
          type="button"
          variant="outline"
          size="icon"
          className="min-h-11 min-w-11"
          onClick={() => setIndice(Math.min(total - 1, indice + 1))}
          disabled={indice >= total - 1}
          aria-label="Imagen siguiente"
        >
          <ChevronRight className="size-4" aria-hidden="true" />
        </Button>
      </div>

      {total > 1 ? (
        <ul className="flex flex-wrap gap-2">
          {imagenes.map((imagen, posicion) => (
            <li key={imagen.id}>
              <button
                type="button"
                onClick={() => setIndice(posicion)}
                aria-current={posicion === indice}
                aria-label={`Ir a la imagen ${posicion + 1} de ${total}`}
                className={cn(
                  "min-h-11 rounded-[var(--radius-sm)] border px-2 text-caption",
                  posicion === indice
                    ? "border-primary bg-surface-raised font-semibold text-foreground"
                    : "border-border text-muted-foreground",
                )}
              >
                {posicion + 1}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
