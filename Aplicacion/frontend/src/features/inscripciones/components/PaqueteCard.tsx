"use client";

import type { UseFormRegisterReturn } from "react-hook-form";
import { Check, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PaqueteCatalogo } from "../types/inscripcion.types";

export interface PaqueteCardProps {
  paquete: PaqueteCatalogo;
  /** Whether this package is the chosen one. */
  seleccionado: boolean;
  /** The registration of the radio that selects this package. */
  registro: UseFormRegisterReturn;
}

/**
 * PaqueteCard - one package of the catalogue.
 *
 * It is a LABEL around a real radio: the browser gives the group the arrow
 * keys, the focus and the announcement for free, and the visitor reaches it
 * with the keyboard.
 *
 * The card prints what the catalogue DECLARES and nothing else:
 *
 * - the cupos the package grants, never a sum;
 * - the price of the catalogue, as the server sends it, never a total
 *   multiplied in the browser;
 * - the disciplines and the benefits that the package offers.
 *
 * A package without a price does not exist in the catalogue of the server:
 * there is no price of reserve here to invent either.
 */
export function PaqueteCard(props: PaqueteCardProps) {
  const paquete = props.paquete;
  const seleccionado = props.seleccionado;
  const registro = props.registro;

  const nombreRadio =
    paquete.nombre + ". " + paquete.cupos_incluidos + " cupos.";

  return (
    <label
      className={cn(
        "flex cursor-pointer flex-col gap-3 rounded-[var(--radius-lg)] border bg-surface-raised p-4 transition-colors",
        "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background",
        seleccionado
          ? "border-primary shadow-[var(--elevation-sm)]"
          : "border-border hover:border-border-strong",
      )}
    >
      <span className="flex items-start gap-3">
        <input
          type="radio"
          name={registro.name}
          value={paquete.id}
          onChange={registro.onChange}
          onBlur={registro.onBlur}
          ref={registro.ref}
          aria-label={nombreRadio}
          className="mt-1 size-4 shrink-0 accent-primary"
        />

        <span className="flex min-w-0 flex-1 flex-col gap-1">
          <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="text-sm font-semibold text-foreground">
              {paquete.nombre}
            </span>
            {seleccionado ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                <Check className="size-3.5" aria-hidden="true" />
                Elegido
              </span>
            ) : null}
          </span>

          {paquete.descripcion ? (
            <span className="text-caption leading-relaxed text-muted-foreground">
              {paquete.descripcion}
            </span>
          ) : null}
        </span>
      </span>

      <span className="flex flex-wrap items-baseline gap-x-4 gap-y-2 border-t border-border pt-3">
        <span className="flex items-center gap-1.5 text-sm text-foreground">
          <Users className="size-4 text-muted-foreground" aria-hidden="true" />
          <span className="tabular-nums">{paquete.cupos_incluidos}</span>
          <span className="text-caption text-muted-foreground">
            {paquete.cupos_incluidos === 1 ? "cupo" : "cupos"}
          </span>
        </span>

        <span className="flex items-baseline gap-1.5">
          <span className="tabular-nums text-sm font-semibold text-foreground">
            {paquete.precio.monto}
          </span>
          <span className="text-caption text-muted-foreground">
            {paquete.precio.moneda}
          </span>
        </span>
      </span>

      {paquete.disciplinas.length > 0 ? (
        <span className="flex flex-wrap gap-1.5">
          {paquete.disciplinas.map((disciplina) => (
            <span
              key={disciplina.id}
              className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground"
            >
              {disciplina.nombre}
            </span>
          ))}
        </span>
      ) : null}

      {paquete.beneficios.length > 0 ? (
        <span className="flex flex-col gap-1">
          {paquete.beneficios.map((beneficio) => (
            <span
              key={beneficio.codigo}
              className="flex items-baseline gap-2 text-caption text-muted-foreground"
            >
              <Check className="size-3.5 shrink-0 text-success" aria-hidden="true" />
              <span>{beneficio.nombre}</span>
              <span className="tabular-nums">{beneficio.cantidad}</span>
            </span>
          ))}
        </span>
      ) : null}
    </label>
  );
}
