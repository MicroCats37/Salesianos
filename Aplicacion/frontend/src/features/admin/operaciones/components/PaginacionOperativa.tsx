import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import type { PaginaOperativa } from "../types/operaciones.types";

export interface PaginacionOperativaProps {
  /** The page of the list, as the server published it. */
  pagina: PaginaOperativa<unknown>;
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
  /** The name of the region, in the words of the operator. */
  etiqueta: string;
}

/**
 * The URL of a page of the list.
 *
 * The page lives in the URL with the rest of the filters, so a page of the
 * list is a link that can be shared (`GOV-02-RB-03b`).
 */
function urlDePagina(
  parametros: Record<string, string>,
  pagina: number,
): string {
  const query = new URLSearchParams({ ...parametros, page: String(pagina) });
  return `?${query.toString()}`;
}

/**
 * PaginacionOperativa - the pagination of an operational list.
 *
 * It is SERVER DRIVEN: the page number travels in the URL and every control
 * is a link. The browser never computes a page, a total or a page size
 * (`SH-01` T-03).
 *
 * The shape is the ONE pagination of the frozen envelope
 * (`FREEZE-ENV-1.0.0` §4.3): `items/total/page/page_size/total_pages`.
 */
export function PaginacionOperativa({
  pagina,
  parametros,
  etiqueta,
}: PaginacionOperativaProps) {
  if (pagina.total_pages <= 1) {
    return null;
  }

  const primero = (pagina.page - 1) * pagina.page_size + 1;
  const ultimo = Math.min(pagina.page * pagina.page_size, pagina.total);
  const paginas = Array.from(
    { length: pagina.total_pages },
    (_, indice) => indice + 1,
  );

  return (
    <div className="flex flex-col gap-3 border-t border-border pt-4">
      <p className="text-sm text-muted-foreground">
        Mostrando{" "}
        <span className="font-medium tabular-nums text-foreground">{primero}</span>{" "}
        a{" "}
        <span className="font-medium tabular-nums text-foreground">{ultimo}</span>{" "}
        de{" "}
        <span className="font-medium tabular-nums text-foreground">
          {pagina.total}
        </span>{" "}
        resultados · página {pagina.page} de {pagina.total_pages}
      </p>

      <Pagination aria-label={etiqueta}>
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              href={urlDePagina(parametros, Math.max(pagina.page - 1, 1))}
              text="Anterior"
              aria-label="Ir a la página anterior"
              aria-disabled={pagina.page === 1}
              className={
                pagina.page === 1 ? "pointer-events-none opacity-50" : undefined
              }
            />
          </PaginationItem>

          {paginas.map((numero) => (
            <PaginationItem key={numero}>
              <PaginationLink
                href={urlDePagina(parametros, numero)}
                isActive={numero === pagina.page}
                aria-label={`Ir a la página ${numero}`}
              >
                {numero}
              </PaginationLink>
            </PaginationItem>
          ))}

          <PaginationItem>
            <PaginationNext
              href={urlDePagina(
                parametros,
                Math.min(pagina.page + 1, pagina.total_pages),
              )}
              text="Siguiente"
              aria-label="Ir a la página siguiente"
              aria-disabled={pagina.page === pagina.total_pages}
              className={
                pagina.page === pagina.total_pages
                  ? "pointer-events-none opacity-50"
                  : undefined
              }
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
}
