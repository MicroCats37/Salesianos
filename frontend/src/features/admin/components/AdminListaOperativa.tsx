"use client";

import type { ReactNode } from "react";
import { Pagination } from "@/components/genericPagination/Pagination";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { AdminOpcionOrden } from "../utils/admin.lista.utils";
import {
  AdminListaError,
  AdminListaSkeleton,
  AdminListaVacia,
} from "./AdminListaEstados";
import { AdminListaToolbar } from "./AdminListaToolbar";

/** A column of an operational table. */
export interface AdminColumna<TItem> {
  /** Stable key of the column. */
  clave: string;
  /** Header of the column. */
  etiqueta: string;
  /** Cell renderer. */
  render: (item: TItem) => ReactNode;
  className?: string;
}

/**
 * How many columns a table must declare to be rendered as a TABLE.
 *
 * A table with this many columns (or more) is only shown from `xl`: below
 * that width the columns are unreadable and the list is rendered as cards.
 * A table with fewer columns keeps the table from `md`.
 */
export const ADMIN_COLUMNAS_MINIMO_PARA_TABLA = 5;

export interface AdminListaOperativaProps<TItem> {
  /** Items of the current page. */
  items: TItem[];
  /** Total number of rows of the filtered list. */
  total: number;
  /** Current page (1-based). */
  pagina: number;
  /** Number of pages of the filtered list. */
  totalPaginas: number;
  /** Page size. */
  pageSize: number;
  /** Whether the query is still running. */
  cargando: boolean;
  /** Error message of the query, if it failed. */
  error: string | null;
  /** Retry action of the query. */
  onReintentar: () => void;
  /** Whether a filter is narrowing the list. */
  hayFiltros: boolean;
  /** How many resource filters are active (the badge of the mobile sheet). */
  filtrosActivos: number;
  onLimpiarFiltros: () => void;
  onCambiarPagina: (pagina: number) => void;
  onCambiarPageSize: (pageSize: number) => void;
  /** Free-text term (owned by the URL). */
  termino: string;
  onBuscar: (termino: string) => void;
  /** Ordering value and options (only whitelisted public fields). */
  orden: string;
  opcionesOrden: AdminOpcionOrden[];
  onCambiarOrden: (orden: string) => void;
  /** Resource filters of the section. */
  controles?: ReactNode;
  /** Columns of the desktop table. */
  columnas: AdminColumna<TItem>[];
  /** Stable key of an item — the identifier the backend assigned to it. */
  claveItem: (item: TItem) => string;
  /** Renderer of the mobile card of an item. */
  renderTarjeta: (item: TItem) => ReactNode;
  /** Action of a row (open the drilldown). */
  onAbrir?: (item: TItem) => void;
  /** Title of the empty state. */
  tituloVacio: string;
  /** Description of the empty state. */
  descripcionVacia: string;
}

/**
 * AdminListaOperativa — the shell of every operational table.
 *
 * It renders the toolbar, the four mandatory states (loading, error, empty,
 * filtered-empty), the DESKTOP table, the MOBILE cards and the pagination.
 *
 * The desktop table and the mobile cards show the SAME items: the layout
 * changes, the data never does.
 */
export function AdminListaOperativa<TItem>({
  items,
  total,
  pagina,
  totalPaginas,
  pageSize,
  cargando,
  error,
  onReintentar,
  hayFiltros,
  filtrosActivos,
  onLimpiarFiltros,
  onCambiarPagina,
  onCambiarPageSize,
  termino,
  onBuscar,
  orden,
  opcionesOrden,
  onCambiarOrden,
  controles,
  columnas,
  claveItem,
  renderTarjeta,
  onAbrir,
  tituloVacio,
  descripcionVacia,
}: AdminListaOperativaProps<TItem>) {
  // A wide table is only a table from `xl`: below that width the same rows
  // are rendered as cards. The decision is derived from the columns, never
  // from a new prop.
  const tablaDesdeXl = columnas.length >= ADMIN_COLUMNAS_MINIMO_PARA_TABLA;
  const clasesTabla = tablaDesdeXl ? "hidden xl:block" : "hidden md:block";
  const clasesCards = tablaDesdeXl ? "flex xl:hidden" : "flex md:hidden";

  return (
    <div className="space-y-4">
      <AdminListaToolbar
        termino={termino}
        onBuscar={onBuscar}
        opcionesOrden={opcionesOrden}
        orden={orden}
        onCambiarOrden={onCambiarOrden}
        hayFiltros={hayFiltros}
        filtrosActivos={filtrosActivos}
        onLimpiarFiltros={onLimpiarFiltros}
      >
        {controles}
      </AdminListaToolbar>

      {cargando ? (
        <AdminListaSkeleton variant={tablaDesdeXl ? "tabla" : "cards"} />
      ) : error ? (
        <AdminListaError mensaje={error} onReintentar={onReintentar} />
      ) : items.length === 0 ? (
        <AdminListaVacia
          titulo={hayFiltros ? "Sin resultados" : tituloVacio}
          descripcion={
            hayFiltros
              ? "No hay resultados para los filtros actuales. Ajusta la búsqueda o limpia los filtros para ver todo."
              : descripcionVacia
          }
          accion={hayFiltros ? "Limpiar filtros" : undefined}
          onAccion={hayFiltros ? onLimpiarFiltros : undefined}
        />
      ) : (
        <>
          {/* Wide table — only from `xl` when the table declares many columns */}
          <div className={cn("card-elevated overflow-hidden", clasesTabla)}>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-slate-100 bg-slate-50/70">
                    {columnas.map((columna) => (
                      <TableHead
                        key={columna.clave}
                        className={cn(
                          "py-3 text-[10px] font-black uppercase tracking-[0.15em] text-slate-500",
                          columna.className,
                        )}
                      >
                        {columna.etiqueta}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((item) => (
                    <TableRow
                      key={claveItem(item)}
                      onClick={onAbrir ? () => onAbrir(item) : undefined}
                      className={cn(
                        "border-b border-slate-50 transition-colors last:border-0 hover:bg-slate-50/70",
                        onAbrir && "cursor-pointer",
                      )}
                    >
                      {columnas.map((columna) => (
                        <TableCell
                          key={columna.clave}
                          className={cn(
                            "py-3.5 text-xs text-slate-700",
                            columna.className,
                          )}
                        >
                          {columna.render(item)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>

          {/* Mobile cards */}
          <div className={cn("flex flex-col gap-3", clasesCards)}>
            {items.map((item) => {
              const tarjeta = renderTarjeta(item);
              const clases = cn(
                "card-elevated w-full p-4 text-left",
                onAbrir && "active:scale-[0.99]",
              );

              /*
                A card WITHOUT a drilldown is not a button: a focusable
                control without an action lies to the keyboard and to the
                screen reader.
              */
              if (!onAbrir) {
                return (
                  <article key={claveItem(item)} className={clases}>
                    {tarjeta}
                  </article>
                );
              }

              return (
                <button
                  key={claveItem(item)}
                  type="button"
                  onClick={() => onAbrir(item)}
                  className={clases}
                >
                  {tarjeta}
                </button>
              );
            })}
          </div>

          <Pagination
            currentPage={pagina}
            totalPages={totalPaginas}
            onPageChange={onCambiarPagina}
            onPageSizeChange={onCambiarPageSize}
            totalItems={total}
            pageSize={pageSize}
          />
        </>
      )}
    </div>
  );
}
