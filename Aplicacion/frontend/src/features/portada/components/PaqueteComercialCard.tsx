"use client";

import { Loader2 } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";
import type { PaqueteListContract } from "@/features/portada/fixtures/paquete.schema";
import { cn } from "@/lib/utils";
import { DisciplinaIcon } from "./DisciplinaIcon";
import {
  type EtapaPrecio,
  formatMonto,
  getColorAcento,
  getDescripcionFallback,
  getDisciplinasOrdenadas,
  getInclusionBullets,
  getLineasPrecio,
} from "./paquete-copy";

export interface PrecioCalculado {
  /** Total a pagar = precio unitario × cantidad. */
  total: number;
  /** Precio por integrante. */
  unitario: number;
  /** Precio regular total (el que se tacha), null cuando no aplica. */
  totalRegular: number | null;
  /** Integrantes cotizados. */
  cantidad: number;
  /**
   * True while the server has not confirmed this figure yet.
   *
   * The total shown is already the optimistic one, so the only thing left to
   * signal is that the confirmation is in flight — never a "waiting" message.
   */
  pendiente?: boolean;
}

export interface PaqueteComercialCardProps {
  paquete: PaqueteListContract;
  variant: "PACK" | "DISCIPLINA";
  selected?: boolean;
  onSelect?: () => void;
  /**
   * When present the price block switches to the computed variant: the BIG
   * number shows the total to pay for the selected quantity instead of the
   * static "precio por integrante" of the catalog.
   */
  precioCalculado?: PrecioCalculado | null;
  /** Etapa de venta: cambia el importe mostrado y el tachado del regular. */
  etapa?: EtapaPrecio;
  footer?: ReactNode;
  className?: string;
}

export function PaqueteComercialCard({
  paquete,
  variant,
  selected = false,
  onSelect,
  precioCalculado,
  etapa = "preventa",
  footer,
  className,
}: PaqueteComercialCardProps) {
  const disciplinas = getDisciplinasOrdenadas(paquete);
  const bullets = getInclusionBullets(paquete);
  const precios = getLineasPrecio(paquete, etapa);
  const descripcion =
    (paquete.descripcion ?? "").trim() || getDescripcionFallback(variant);
  const accentColor = getColorAcento(paquete);

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!onSelect || event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect();
    }
  };

  return (
    <article
      className={cn(
        "group flex h-full flex-col overflow-hidden rounded-2xl bg-surface-raised shadow-[0_8px_30px_color-mix(in_srgb,var(--brand-deep-navy)_10%,transparent)] ring-1 ring-border/70 transition-[box-shadow,transform] duration-300 hover:-translate-y-0.5 hover:shadow-[0_12px_36px_color-mix(in_srgb,var(--brand-deep-navy)_16%,transparent)]",
        selected && "ring-2 ring-primary",
        onSelect && "cursor-pointer",
        className,
      )}
      data-variant={variant}
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
    >
      <div className="flex flex-1 flex-col p-4 sm:p-5">
        {/* The title drops below the icons when the card is too narrow for both:
            a clipped package name is worse than an extra line. */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          {disciplinas.length > 0 && (
            <div className="flex shrink-0 items-center">
              {disciplinas.map((disciplina, index) => (
                <DisciplinaIcon
                  key={disciplina.disciplina_id}
                  sigla={disciplina.disciplina_sigla}
                  label={disciplina.disciplina_nombre}
                  className={cn(index > 0 && "-ml-2")}
                />
              ))}
            </div>
          )}
          <div className="min-w-[9rem] flex-1">
            <h3 className="line-clamp-2 text-[14px] font-black uppercase leading-tight tracking-tight text-foreground">
              {paquete.nombre}
            </h3>
            {selected && (
              <span className="mt-1 inline-flex items-center rounded-full bg-primary px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-primary-foreground">
                Seleccionado
              </span>
            )}
          </div>
        </div>

        <p className="mt-3 line-clamp-2 text-[13px] leading-snug text-muted-foreground">
          {descripcion}
        </p>

        <div className="mt-3 rounded-xl bg-surface p-3.5">
          <p className="font-bold text-[13px] text-foreground">Incluye:</p>
          <ul className="mt-2 space-y-1.5">
            {bullets.map((bullet) => (
              <li
                key={bullet.texto}
                className="flex items-start gap-2 text-[12.5px] leading-[1.55] text-foreground"
              >
                <span
                  className="mt-[0.52em] size-1 shrink-0 rounded-full bg-primary"
                  aria-hidden="true"
                />
                <span className={cn(bullet.destacado && "font-bold")}>
                  {bullet.texto}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="my-4 border-t border-border" />

        <div className="mt-auto text-center">
          {precioCalculado ? (
            <>
              <p className="text-[14px] font-bold text-primary">
                {precioCalculado.cantidad} integrantes
              </p>
              {precioCalculado.totalRegular != null && (
                <p className="text-[12.5px] font-semibold text-destructive">
                  Precio regular{" "}
                  <span className="line-through">
                    {formatMonto(precioCalculado.totalRegular)}
                  </span>
                </p>
              )}
              <p className="flex items-center justify-center gap-1.5 text-[26px] font-black leading-tight text-foreground">
                {formatMonto(precioCalculado.total)}
                {precioCalculado.pendiente && (
                  <Loader2
                    className="size-3.5 shrink-0 animate-spin text-primary/70"
                    aria-label="Cotizacion en curso"
                  />
                )}
              </p>
              <p className="text-[12px] font-semibold text-muted-foreground">
                {formatMonto(precioCalculado.unitario)} x integrante
              </p>
            </>
          ) : (
            <>
              <p className="text-[14px] font-bold text-primary">
                {precios.total}
              </p>
              {precios.totalRegular && (
                <p className="text-[12.5px] font-semibold text-destructive">
                  Precio regular{" "}
                  <span className="line-through">{precios.totalRegular}</span>
                </p>
              )}
              <p className="text-[21px] font-black text-foreground">
                {precios.unitario}
              </p>
            </>
          )}
        </div>

        {footer && <div className="mt-4">{footer}</div>}
      </div>

      <div
        className="h-2 w-full shrink-0"
        style={{ backgroundColor: accentColor }}
        aria-hidden="true"
      />
    </article>
  );
}
