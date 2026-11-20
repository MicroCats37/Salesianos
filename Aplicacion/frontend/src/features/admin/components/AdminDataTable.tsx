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

export interface AdminColumna {
  /** The stable key of the column. */
  key: string;
  /** The name of the column, in sentence case. */
  label: string;
  /** Extra classes of the header cell. */
  className?: string;
  /**
   * Whether the column holds a quantity, a price or a date.
   *
   * A number aligns to the right and uses the TABULAR figures, so the
   * column can be compared down instead of read across.
   */
  numerico?: boolean;
  /** Whether the column holds an identifier: it uses the monospace face. */
  identificador?: boolean;
}

/** One row of the table: its cells, keyed by the column key. */
export interface AdminFila {
  /** The content of each cell, keyed by the column key. */
  cells: Record<string, ReactNode>;
}

export interface AdminDataTableProps {
  /** The columns of the table. */
  columns: AdminColumna[];
  /** The caption of the table: what the table lists. */
  caption: string;
  /** The rows of the table. */
  filas?: AdminFila[];
  /** What the table shows when there are no rows. */
  vacio?: ReactNode;
}

/**
 * The typography of a cell, derived from the column.
 *
 * The contract is the same for every table of the area: quantities align to
 * the right with tabular figures, identifiers wear the monospace face and
 * the rest is prose.
 */
function claseCelda(columna: AdminColumna): string {
  return cn(
    columna.numerico && "text-right tabular-nums",
    columna.identificador && "font-mono text-xs tracking-tight",
  );
}

/**
 * AdminDataTable - the table of an administration block.
 *
 * The header is the contract of the block: it says what the operator is
 * going to read, even when the table is still empty. The empty state lives
 * INSIDE the table, spanning every column, so the layout does not jump
 * when the rows arrive.
 *
 * The table never overflows the page: the container scrolls sideways, which
 * keeps the meaning of every column on a narrow screen.
 */
export function AdminDataTable({
  columns,
  caption,
  filas,
  vacio,
}: AdminDataTableProps) {
  return (
    <Table className="rounded-[var(--radius-md)]">
      <TableCaption className="sr-only">{caption}</TableCaption>
      <TableHeader>
        <TableRow className="hover:border-l-transparent hover:bg-transparent">
          {columns.map((columna) => (
            <TableHead
              key={columna.key}
              className={cn(
                "h-11 bg-muted/50 text-xs font-semibold tracking-[0.04em] text-muted-foreground",
                columna.numerico && "text-right tabular-nums",
                columna.className,
              )}
            >
              {columna.label}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {filas && filas.length > 0 ? (
          filas.map((fila, indice) => (
            <TableRow key={indice}>
              {columns.map((columna) => (
                <TableCell key={columna.key} className={claseCelda(columna)}>
                  {fila.cells[columna.key]}
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <TableRow className="hover:border-l-transparent hover:bg-transparent">
            <TableCell
              colSpan={columns.length}
              className="whitespace-normal p-0"
            >
              {vacio}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
