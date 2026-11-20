"use client";

import { TriangleAlert } from "lucide-react";
import type { PoolInscripcion } from "../types/inscripcion.types";

export interface PanelPoolProps {
  /** The pool, exactly as the server publishes it. */
  pool: PoolInscripcion | null;
}

function Numero(props: { valor: number; etiqueta: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="text-2xl font-bold tabular-nums text-foreground">
        {props.valor}
      </span>
      <span className="text-caption text-muted-foreground">{props.etiqueta}</span>
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
      <div className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="grid grid-cols-3 gap-4">
          <Numero valor={pool.cupos_pagados} etiqueta="cupos pagados" />
          <Numero valor={pool.cupos_asignados} etiqueta="cupos asignados" />
          <Numero valor={pool.cupos_disponibles} etiqueta="cupos disponibles" />
        </div>

        <p className="max-w-measure text-sm leading-relaxed text-foreground">
          {balance}
        </p>
      </div>

      {pool.cupos_pagados === 0 ? (
        <p className="text-sm leading-relaxed text-foreground">
          No hay ningún cupo habilitado todavía. Los cupos se habilitan
          cuando el pago se confirme.
        </p>
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
