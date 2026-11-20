"use client";

import { ChevronLeft, ChevronRight, ImageOff } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ImagenPatrocinador } from "../types/patrocinador.types";

export interface GaleriaPatrocinadorProps {
  /** The ordered gallery of the sponsor. */
  imagenes: ImagenPatrocinador[];
  className?: string;
}

/**
 * GaleriaPatrocinador - the ordered gallery of a sponsor.
 *
 * The order of the array IS the canonical order of the images (`FR-06`
 * §2.4): the gallery never renumbers them and never sorts them on its own.
 *
 * It is composed with the local `button` primitive instead of the registry
 * `carousel`: the local carousel ships the English screen-reader labels
 * "Previous slide" and "Next slide", and `components/ui/**` is a forbidden
 * root of this packet (`A0-UI03-01`).
 *
 * The gallery is KEYBOARD operable: the two controls are buttons with a
 * Spanish accessible name, the thumbnails are buttons with `aria-current`
 * and the position is announced in a live region (`RB-08` ADM-21).
 */
export function GaleriaPatrocinador({
  imagenes,
  className,
}: GaleriaPatrocinadorProps) {
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
          <span className="text-caption">
            Este patrocinador todavía no tiene piezas
          </span>
        </span>
      </div>
    );
  }

  // The URL and the availability are TWO facts and the gap is shown when
  // EITHER of them fails: a file that is not readable has no URL to draw.
  const archivo = actual.disponible && actual.url ? actual.url : null;

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="relative aspect-[4/3] overflow-hidden rounded-[var(--radius-lg)] bg-surface-recessed">
        {archivo ? (
          <img
            src={archivo}
            alt={actual.texto_alternativo}
            className="size-full object-cover"
          />
        ) : (
          <span className="flex size-full flex-col items-center justify-center gap-1 text-muted-foreground">
            <ImageOff className="size-5" aria-hidden="true" />
            <span className="text-caption">
              {actual.texto_alternativo ||
                "La imagen no está disponible en el servidor"}
            </span>
          </span>
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
          aria-label="Pieza anterior"
        >
          <ChevronLeft className="size-4" aria-hidden="true" />
        </Button>

        <p aria-live="polite" className="text-caption text-muted-foreground">
          {`Pieza ${indice + 1} de ${total}`}
        </p>

        <Button
          type="button"
          variant="outline"
          size="icon"
          className="min-h-11 min-w-11"
          onClick={() => setIndice(Math.min(total - 1, indice + 1))}
          disabled={indice >= total - 1}
          aria-label="Pieza siguiente"
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
                aria-label={`Ir a la pieza ${posicion + 1} de ${total}`}
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
