"use client";

import { Ticket } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PaseCatalogo } from "../schemas";
import {
  formatearMontoPase,
  paseCantidadLimite,
  paseComprable,
  paseEtapaVigente,
  paseHoyLocal,
  pasePrecioUnitario,
} from "../utils/pase.precio";

/**
 * PaseCatalogoCard — ONE pass of the public catalogue.
 *
 * The card is DISPLAY-ONLY: it reports the price the backend froze and never
 * computes a price of its own. The selection is a real button with
 * `aria-pressed`, so the keyboard and the screen readers announce which pass
 * is chosen.
 */

export interface PaseCatalogoCardProps {
  /** The pass of the card. */
  pase: PaseCatalogo;
  /** Whether this card is the selected one. */
  seleccionado: boolean;
  /** Called when the buyer selects the pass. */
  onSeleccionar: (pase: PaseCatalogo) => void;
  /** Whether the selection is blocked (a purchase is in flight). */
  deshabilitado?: boolean;
  /** ISO date used to resolve the stage of the price — defaults to today. */
  hoy?: string;
}

export function PaseCatalogoCard({
  pase,
  seleccionado,
  onSeleccionar,
  deshabilitado = false,
  hoy,
}: PaseCatalogoCardProps) {
  const comprable = paseComprable(pase);
  const precio = pasePrecioUnitario(pase);
  const etapa = paseEtapaVigente(pase, hoy ?? paseHoyLocal());
  const limite = paseCantidadLimite(pase);

  return (
    <article
      className={`flex h-full flex-col gap-4 rounded-3xl border p-5 transition ${
        seleccionado
          ? "border-[#312e8e] bg-[#312e8e]/[0.04] shadow-lg"
          : "border-slate-200 bg-white"
      }`}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Ticket
            className="size-5 shrink-0 text-[#312e8e]"
            aria-hidden="true"
          />
          <h3 className="text-base font-black text-slate-900">{pase.nombre}</h3>
        </div>
        {etapa ? (
          <Badge variant="outline" className="shrink-0 font-bold">
            {etapa.etapa}
          </Badge>
        ) : null}
      </header>

      {pase.descripcion ? (
        <p className="text-sm leading-relaxed text-slate-600">
          {pase.descripcion}
        </p>
      ) : null}

      <p className="text-2xl font-black text-[#312e8e]">
        {formatearMontoPase(precio)}
        <span className="ml-1 text-xs font-bold uppercase tracking-wider text-slate-500">
          por pase
        </span>
      </p>

      <p className="text-xs font-medium text-slate-500">
        {pase.cantidad_maxima > 0
          ? `Inventario limitado a ${pase.cantidad_maxima} pases.`
          : "Pases sin límite de inventario."}
        {` Máximo ${limite} por compra.`}
      </p>

      <div className="mt-auto">
        <Button
          type="button"
          onClick={() => onSeleccionar(pase)}
          disabled={!comprable || deshabilitado}
          aria-pressed={seleccionado}
          variant={seleccionado ? "default" : "outline"}
          className="w-full rounded-full font-black"
        >
          {comprable
            ? seleccionado
              ? "Pase seleccionado"
              : "Seleccionar"
            : "No disponible"}
        </Button>
      </div>
    </article>
  );
}
