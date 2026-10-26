"use client";

import { useCallback } from "react";
import {
  type AdminEstadoLista,
  adminHayFiltrosActivos,
} from "../utils/admin.lista.utils";
import { useAdminListaUrl } from "./useAdminListaUrl";

export interface AdminControlLista {
  /** Current state of the list, read from the URL. */
  estado: AdminEstadoLista;
  /** Whether a filter is narrowing the list. */
  hayFiltros: boolean;
  /**
   * How many RESOURCE filters are narrowing the list.
   *
   * The free-text term is NOT counted: it has its own visible input, so the
   * badge of the mobile filters sheet counts only the filters that are
   * hidden behind it.
   */
  contadorFiltros: number;
  onBuscar: (termino: string) => void;
  onCambiarOrden: (orden: string) => void;
  onCambiarPagina: (pagina: number) => void;
  onCambiarPageSize: (pageSize: number) => void;
  onLimpiarFiltros: () => void;
  /** Sets (or clears, with an empty value) ONE resource filter. */
  onFiltro: (clave: string, valor: string) => void;
  /** Sets (or clears) SEVERAL resource filters at once. */
  onFiltros: (filtros: Record<string, string | undefined>) => void;
}

/**
 * useAdminControlLista — the URL contract of every operational list.
 *
 * It centralises the three rules the sections must NOT repeat:
 * - a new filter, term or ordering returns to the FIRST page,
 * - the page size is always part of the URL,
 * - "Limpiar filtros" removes the term and every resource filter.
 */
export function useAdminControlLista(
  prefijo = "",
  otros: string[] = [],
): AdminControlLista {
  const { estado, actualizar, limpiar } = useAdminListaUrl(prefijo, otros);

  const onBuscar = useCallback(
    (termino: string) => {
      actualizar({ q: termino, page: 1 });
    },
    [actualizar],
  );

  const onCambiarOrden = useCallback(
    (orden: string) => {
      actualizar({ ordering: orden, page: 1 });
    },
    [actualizar],
  );

  const onCambiarPagina = useCallback(
    (pagina: number) => {
      actualizar({ page: pagina });
    },
    [actualizar],
  );

  const onCambiarPageSize = useCallback(
    (pageSize: number) => {
      actualizar({ pageSize, page: 1 });
    },
    [actualizar],
  );

  const onLimpiarFiltros = useCallback(() => {
    limpiar();
  }, [limpiar]);

  const onFiltro = useCallback(
    (clave: string, valor: string) => {
      actualizar({ filtros: { [clave]: valor }, page: 1 });
    },
    [actualizar],
  );

  const onFiltros = useCallback(
    (filtros: Record<string, string | undefined>) => {
      actualizar({ filtros, page: 1 });
    },
    [actualizar],
  );

  return {
    estado,
    hayFiltros: adminHayFiltrosActivos(estado),
    contadorFiltros: Object.values(estado.filtros).filter(
      (valor) => String(valor ?? "").trim() !== "",
    ).length,
    onBuscar,
    onCambiarOrden,
    onCambiarPagina,
    onCambiarPageSize,
    onLimpiarFiltros,
    onFiltro,
    onFiltros,
  };
}
