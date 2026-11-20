"use client";

import { Check, Loader2 } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PaqueteCatalogo } from "../types/inscripcion.types";
import {
  getColorAcento,
  getDisciplinasOrdenadas,
  getInclusionBullets,
} from "../utils/paquete-copy";
import { DisciplinaIcon } from "./DisciplinaIcon";

/**
 * The figures of the card when the server has answered a quotation.
 *
 * The TOTAL is the answer of the SERVER: the browser never multiplies a
 * price by a quantity. The unit price and the total arrive as strings and
 * they are printed exactly as they came.
 */
export interface PrecioCalculado {
  /** The total that the server quoted. */
  total: string;
  /** The unit price that the server quoted. */
  unitario: string;
  /** The quantity that was quoted. */
  cantidad: number;
  /** Whether the server has not confirmed the figure yet. */
  pendiente?: boolean;
}

export interface PaqueteComercialCardProps {
  paquete: PaqueteCatalogo;
  selected?: boolean;
  onSelect?: () => void;
  /** The figures of the quotation, when the server has answered. */
  precioCalculado?: PrecioCalculado | null;
  /** The content of the foot of the card (the quantity, for the chosen one). */
  footer?: ReactNode;
  className?: string;
}

/**
 * PaqueteComercialCard - one package of the catalogue.
 *
 * It is COPIED from the previous frontend (`frontend/src/components/
 * paquetes/PaqueteComercialCard.tsx`) and adapted:
 *
 * - the marks of the disciplines come from the `slug` and the `nombre` that
 *   the catalogue publishes (the target backend publishes no `sigla`);
 * - the colours are TOKENS, never literals;
 * - the card prints the amount of the catalogue as it arrives and the total
 *   of the QUOTATION when the server has answered: the browser never sums.
 */
export function PaqueteComercialCard({
  paquete,
  selected = false,
  onSelect,
  precioCalculado,
  footer,
  className,
}: PaqueteComercialCardProps) {
  const disciplinas = getDisciplinasOrdenadas(paquete);
  const bullets = getInclusionBullets(paquete);
  const accentColor = getColorAcento(paquete);

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!onSelect || event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  };

  return (
    // biome-ignore lint/a11y/useAriaPropsSupportedByRole: la tarjeta toma el rol "button" cuando es seleccionable y `aria-pressed` es válido en ese rol; el análisis estático no puede resolver el condicional del rol.
    <article
      className={cn(
        "group flex h-full flex-col overflow-hidden rounded-[var(--radius-lg)] bg-card shadow-[var(--elevation-sm)] ring-1 ring-border transition-colors duration-(--motion-duration-fast) hover:ring-border-strong",
        selected && "ring-2 ring-accent shadow-[var(--elevation-md)]",
        onSelect && "cursor-pointer",
        className,
      )}
      data-paquete-card
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      aria-pressed={onSelect ? selected : undefined}
      aria-label={onSelect ? paquete.nombre : undefined}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
    >
      <div className="flex flex-1 flex-col p-4">
        {/*
         * The title drops below the marks when the card is too narrow for
         * both: a clipped package name is worse than an extra line.
         */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          {disciplinas.length > 0 && (
            <div className="flex shrink-0 items-center">
              {disciplinas.map((disciplina, index) => (
                <DisciplinaIcon
                  key={disciplina.id}
                  disciplina={disciplina}
                  label={disciplina.nombre}
                  className={cn(index > 0 && "-ml-2")}
                />
              ))}
            </div>
          )}
          <div className="min-w-[9rem] flex-1">
            <h3 className="font-heading line-clamp-2 text-sm font-semibold leading-tight text-foreground">
              {paquete.nombre}
            </h3>
            {/*
             * The selection is said with a SHAPE and with WORDS: a check
             * inside a badge that reads "Seleccionado". The ring of the card
             * is the second signal and the `aria-pressed` is the third.
             */}
            {selected && (
              <Badge
                variant="outline"
                className="mt-1 gap-1 border-accent bg-accent/15 text-xs font-semibold text-accent-foreground"
              >
                <Check className="size-3.5" aria-hidden="true" />
                Seleccionado
              </Badge>
            )}
          </div>
        </div>

        {paquete.descripcion ? (
          <p className="mt-3 line-clamp-2 text-caption leading-snug text-muted-foreground">
            {paquete.descripcion}
          </p>
        ) : null}

        {/*
         * "Incluye": what the package OFFERS. The catalogue declares the
         * benefits and the browser only prints them.
         */}
        {bullets.length > 0 ? (
          <div className="mt-3 rounded-[var(--radius-md)] bg-muted/50 p-3.5">
            <p className="text-xs font-semibold text-foreground">Incluye:</p>
            <ul className="mt-2 space-y-1.5">
              {bullets.map((bullet) => (
                <li
                  key={bullet.texto}
                  className="flex items-start gap-2 text-caption leading-[1.55] text-foreground"
                >
                  <span
                    aria-hidden="true"
                    className="mt-[0.52em] size-1 shrink-0 rounded-full bg-primary"
                  />
                  <span className={cn(bullet.destacado && "font-bold")}>
                    {bullet.texto}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="my-4 border-t border-border" />

        <div className="mt-auto text-center">
          {precioCalculado ? (
            <>
              <p className="text-eyebrow-brand text-info">
                {precioCalculado.cantidad} integrantes
              </p>
              <p className="flex items-center justify-center gap-1.5 text-3xl font-bold leading-tight tabular-nums text-foreground">
                {precioCalculado.total}
                {precioCalculado.pendiente && (
                  <Loader2
                    className="size-3.5 shrink-0 animate-spin text-primary/70"
                    aria-label="Cotización en curso"
                  />
                )}
              </p>
              <p className="text-xs font-semibold text-muted-foreground">
                {precioCalculado.unitario} x integrante
              </p>
            </>
          ) : (
            <>
              <p className="text-eyebrow-brand text-info">
                {paquete.cupos_incluidos}{" "}
                {paquete.cupos_incluidos === 1 ? "cupo" : "cupos"}
              </p>
              <p className="text-2xl font-bold tabular-nums text-foreground">
                {paquete.precio.monto} {paquete.precio.moneda}
              </p>
              <p className="text-xs font-semibold text-muted-foreground">
                por integrante
              </p>
            </>
          )}
        </div>

        {footer && <div className="mt-4">{footer}</div>}
      </div>

      {/*
       * The accent strip of the brand: the colour of the discipline at the
       * foot of the card. It is the gesture that the previous frontend had
       * and it is what makes the row of cards read as a catalogue.
       *
       * It is the ONE documented exception to the rule of semantic colours:
       * the accent is RUNTIME DATA that comes from the catalogue of the
       * edition (`utils/paquete-copy.ts`), it is not a role of the theme and
       * it cannot be a token.
       */}
      <div
        className="h-2 w-full shrink-0"
        style={{ backgroundColor: accentColor }}
        aria-hidden="true"
      />
    </article>
  );
}
