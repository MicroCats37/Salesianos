import type { ReactNode } from "react";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { ColumnaOperativa, FilaOperativa } from "../types/operaciones.types";

/**
 * The classes of a cell, derived from the column.
 *
 * The contract is the same for every operational list: quantities align to
 * the right with TABULAR figures, identifiers wear the monospace face and
 * the rest is prose that may wrap.
 */
function clasesCelda(columna: ColumnaOperativa): string {
  return cn(
    columna.numerico && "text-right tabular-nums",
    columna.identificador && "font-mono text-xs tracking-tight",
  );
}

/**
 * The classes of a COLUMN, derived from its priority.
 *
 * A column of priority `2` appears from 1024 and a column of priority `3`
 * appears from 1280. The same header and the same cell disappear together,
 * so the table never loses the alignment of a column.
 */
function clasesPrioridad(columna: ColumnaOperativa): string {
  if (columna.prioridad === 3) return "hidden xl:table-cell";
  if (columna.prioridad === 2) return "hidden lg:table-cell";
  return "";
}

/**
 * The columns that the CARD shows.
 *
 * A card has room for the ESSENTIAL facts of the row, never for the whole
 * row: the columns of priority `2` and `3` are the ones that only make sense
 * side by side with the rest of the table.
 */
function columnasDeTarjeta(columnas: ColumnaOperativa[]): ColumnaOperativa[] {
  return columnas.filter((columna) => (columna.prioridad ?? 1) === 1);
}

export interface ListaOperativaProps {
  /** What the list shows, in one sentence. It is the caption of the table. */
  caption: string;
  /** The columns of the list. */
  columnas: ColumnaOperativa[];
  /** The rows of the list. */
  filas?: FilaOperativa[];
  /** What the list shows when there is nothing to show. */
  vacio?: ReactNode;
  className?: string;
}

/**
 * ListaOperativa - THE list of the administration area.
 *
 * `GOV-02-RB-03a`: the six lists of the panel share ONE pattern, not six.
 * The component answers at every width with the SAME data:
 *
 * - 360 and 390: one card per row, with the title, the state and the
 *   essential context. No horizontal scroll, no hover-only action.
 * - 768: a table with the priority columns.
 * - 1024 and above: the columns of priority `2`.
 * - 1280 and above: every column.
 *
 * The table scrolls INSIDE its own container, so the page never overflows.
 * Every header is a `<th scope="col">` and the key of a row is its stable
 * identifier, never the index (`GOV-02-RB-06d`).
 */
export function ListaOperativa({
  caption,
  columnas,
  filas,
  vacio,
  className,
}: ListaOperativaProps) {
  const tieneFilas = Array.isArray(filas) && filas.length > 0;

  if (!tieneFilas) {
    return <div className={className}>{vacio}</div>;
  }

  const titular = columnas.find((columna) => columna.titular) ?? columnas[0];
  const resto = columnasDeTarjeta(columnas).filter(
    (columna) => columna.key !== titular.key,
  );

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {/* 360 - 390 - one card per row. */}
      <ul className="flex list-none flex-col gap-3 md:hidden">
        {filas.map((fila) => (
          <li
            key={fila.id}
            data-operacion="fila"
            className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 shadow-[var(--elevation-sm)]"
          >
            <p className="text-sm leading-snug font-semibold text-foreground">
              {fila.celdas[titular.key]}
            </p>
            {resto.length > 0 ? (
              <dl className="grid grid-cols-1 gap-x-4 gap-y-2">
                {resto.map((columna) => (
                  <div key={columna.key} className="flex flex-col gap-0.5">
                    <dt className="text-xs text-foreground-muted">
                      {columna.label}
                    </dt>
                    <dd className="text-sm leading-snug text-foreground">
                      {fila.celdas[columna.key]}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </li>
        ))}
      </ul>

      {/* 768 and above - the table, with its priority columns. */}
      <div className="hidden md:block">
        <Table>
          <TableCaption className="sr-only">{caption}</TableCaption>
          <TableHeader>
            <TableRow className="hover:border-l-transparent hover:bg-transparent">
              {columnas.map((columna) => (
                <TableHead
                  key={columna.key}
                  scope="col"
                  className={cn(
                    "h-11 bg-surface-recessed text-xs font-semibold tracking-[0.04em] text-foreground-muted",
                    columna.numerico && "text-right tabular-nums",
                    clasesPrioridad(columna),
                  )}
                >
                  {columna.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filas.map((fila) => (
              <TableRow key={fila.id}>
                {columnas.map((columna) => (
                  <TableCell
                    key={columna.key}
                    className={cn(
                      clasesCelda(columna),
                      "whitespace-normal",
                      clasesPrioridad(columna),
                    )}
                  >
                    {fila.celdas[columna.key]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
