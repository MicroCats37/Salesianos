import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ColumnaOperativa } from "../types/operaciones.types";

export interface EsqueletoOperativoProps {
  /** The columns of the list the skeleton mirrors. */
  columnas: ColumnaOperativa[];
  /** How many rows the skeleton shows. */
  filas?: number;
}

/**
 * EsqueletoOperativo - the S-01 state of an operational list.
 *
 * `SH-03` S-01: the skeleton MIRRORS the final geometry. A centred spinner
 * over an empty page is forbidden, and so is a skeleton that does not look
 * like the list it replaces.
 *
 * The skeleton therefore has the two compositions of `ListaOperativa`: cards
 * at 360 and 390, and a table from 768.
 */
export function EsqueletoOperativo({
  columnas,
  filas = 5,
}: EsqueletoOperativoProps) {
  const indices = Array.from({ length: filas }, (_, indice) => indice);

  return (
    <div className="flex flex-col gap-4">
      <ul className="flex list-none flex-col gap-3 md:hidden" aria-hidden="true">
        {indices.map((indice) => (
          <li
            key={indice}
            className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </li>
        ))}
      </ul>

      <div className="hidden md:block" aria-hidden="true">
        <Table>
          <TableHeader>
            <TableRow className="hover:border-l-transparent hover:bg-transparent">
              {columnas.map((columna) => (
                <TableHead
                  key={columna.key}
                  scope="col"
                  className="h-11 bg-surface-recessed text-xs font-semibold text-foreground-muted"
                >
                  <Skeleton className="h-3 w-20" />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {indices.map((indice) => (
              <TableRow key={indice}>
                {columnas.map((columna) => (
                  <TableCell key={columna.key}>
                    <Skeleton className="h-4 w-28" />
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
