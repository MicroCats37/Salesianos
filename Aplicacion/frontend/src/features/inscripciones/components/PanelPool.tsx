"use client";

import type { LucideIcon } from "lucide-react";
import { CircleCheck, Ticket, TriangleAlert, Users } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import type { PoolInscripcion } from "../types/inscripcion.types";

export interface PanelPoolProps {
  /** The pool, exactly as the server publishes it. */
  pool: PoolInscripcion | null;
}

/**
 * One of the three figures that the server declared.
 *
 * The figure is the HERO of the tile and the label is its caption: the
 * visitor reads the balance of the cupos at a glance. The icon says which
 * figure it is, so the three tiles are distinguishable without the colour.
 */
function Cifra(props: {
  valor: number;
  etiqueta: string;
  Icono: LucideIcon;
  tono: string;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-3 sm:p-4">
      <span
        aria-hidden="true"
        className={cn(
          "flex size-9 items-center justify-center rounded-full bg-muted",
          props.tono,
        )}
      >
        <props.Icono className="size-4" />
      </span>
      <span className="text-3xl font-bold leading-none tabular-nums text-foreground">
        {props.valor}
      </span>
      <span className="text-caption text-muted-foreground">
        {props.etiqueta}
      </span>
    </div>
  );
}

/**
 * PanelPool - the balance of the cupos of a registration.
 *
 * The three numbers are the ANSWER of the server (RN-I03): the browser
 * prints them side by side and NEVER subtracts them. The sentence next to
 * the band reads the same three numbers as a phrase, so a screen reader
 * hears the balance instead of three isolated figures.
 *
 * The cause and the impediments are the words of the backend. The
 * component prints `mensaje` verbatim and never branches on `codigo`: the
 * catalogue of public codes is not closed, so a new code would break a
 * component that decided what it means.
 */
export function PanelPool(props: PanelPoolProps) {
  const pool = props.pool;

  if (!pool) {
    return (
      <p className="text-sm text-muted-foreground">
        El balance de cupos todavía no está disponible.
      </p>
    );
  }

  const balance =
    pool.cupos_pagados +
    " cupos pagados, " +
    pool.cupos_asignados +
    " asignados y " +
    pool.cupos_disponibles +
    " disponibles.";

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-4 rounded-[var(--radius-xl)] border border-border bg-surface-recessed p-4 sm:p-5">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Cifra
            valor={pool.cupos_pagados}
            etiqueta="cupos pagados"
            Icono={CircleCheck}
            tono="text-success"
          />
          <Cifra
            valor={pool.cupos_asignados}
            etiqueta="cupos asignados"
            Icono={Users}
            tono="text-primary"
          />
          <Cifra
            valor={pool.cupos_disponibles}
            etiqueta="cupos disponibles"
            Icono={Ticket}
            tono="text-info"
          />
        </div>

        <p className="max-w-measure text-sm leading-relaxed text-foreground">
          {balance}
        </p>
      </div>

      {pool.cupos_pagados === 0 ? (
        <Alert className="border-info/45 bg-info/12">
          <TriangleAlert className="size-4 text-info" aria-hidden="true" />
          <AlertTitle className="text-foreground">
            Ningún cupo habilitado todavía
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            No hay ningún cupo habilitado todavía. Los cupos se habilitan cuando
            el pago se confirme.
          </AlertDescription>
        </Alert>
      ) : null}

      <p className="text-caption text-muted-foreground">
        Causa de la respuesta: {pool.causa_operativa}
      </p>

      {pool.impedimentos.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {pool.impedimentos.map((impedimento) => (
            <li
              key={impedimento.codigo + impedimento.mensaje}
              className="flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/45 bg-warning/12 px-3 py-2.5"
            >
              <TriangleAlert
                className="mt-0.5 size-4 shrink-0 text-warning"
                aria-hidden="true"
              />
              <span className="text-sm leading-relaxed text-foreground">
                {impedimento.mensaje}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
