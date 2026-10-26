"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import {
  type AdminEstadoLista,
  adminEstadoDesdeParametros,
  adminParametrosUrlActualizados,
} from "../utils/admin.lista.utils";

/**
 * useAdminListaUrl — the URL owns the state of every administration list.
 *
 * Filters, pagination and ordering live in the query string, NOT in a local
 * state: a list can be shared, bookmarked and navigated back and forth
 * without losing its context.
 *
 * The hook only exposes three things:
 * - `estado`: the current state, read from the URL,
 * - `actualizar`: a partial update that writes the URL,
 * - `limpiar`: the "Limpiar filtros" action.
 *
 * `prefijo` gives the list its own NAMESPACE of URL parameters, so a page
 * with two lists (the people and the roster rows) never sends the filters of
 * one tab to the endpoint of the other one. `otros` lists the prefixes of the
 * SIBLING namespaces, whose parameters must survive an update of this one.
 */
export function useAdminListaUrl(prefijo = "", otros: string[] = []) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const estado = useMemo(
    () => adminEstadoDesdeParametros(searchParams, prefijo, otros),
    [searchParams, prefijo, otros],
  );

  const actualizar = useCallback(
    (
      cambios: Partial<Omit<AdminEstadoLista, "filtros">> & {
        filtros?: Record<string, string | undefined>;
      },
    ) => {
      const filtros = { ...estado.filtros };

      for (const [clave, valor] of Object.entries(cambios.filtros ?? {})) {
        const limpio = String(valor ?? "").trim();
        if (limpio) {
          filtros[clave] = limpio;
        } else {
          delete filtros[clave];
        }
      }

      const siguiente: AdminEstadoLista = {
        page: cambios.page ?? estado.page,
        pageSize: cambios.pageSize ?? estado.pageSize,
        q: cambios.q ?? estado.q,
        ordering: cambios.ordering ?? estado.ordering,
        filtros,
      };

      const parametros = adminParametrosUrlActualizados(
        searchParams,
        siguiente,
        prefijo,
        otros,
      );
      const query = parametros.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, {
        scroll: false,
      });
    },
    [estado, otros, pathname, prefijo, router, searchParams],
  );

  const limpiar = useCallback(() => {
    const parametros = adminParametrosUrlActualizados(
      searchParams,
      {
        page: 1,
        // The page size is NOT a filter: the choice of the administrator
        // survives a "Limpiar filtros".
        pageSize: estado.pageSize,
        q: "",
        ordering: "",
        filtros: {},
      },
      prefijo,
      otros,
    );
    const query = parametros.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }, [estado.pageSize, otros, pathname, prefijo, router, searchParams]);

  return { estado, actualizar, limpiar };
}

/**
 * useAdminDetalleUrl — the drilldown sheet of a row is also URL-owned.
 *
 * The open detail lives in the `detalle` parameter, so a drilldown can be
 * shared and the browser back button closes it. It is NOT a resource filter:
 * it never reaches the backend.
 */
export function useAdminDetalleUrl(prefijo = "") {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const detalleId = searchParams.get(`${prefijo}detalle`) ?? "";

  const abrirDetalle = useCallback(
    (id: string) => {
      const parametros = new URLSearchParams(searchParams.toString());
      parametros.set(`${prefijo}detalle`, id);
      router.replace(`${pathname}?${parametros.toString()}`, { scroll: false });
    },
    [pathname, prefijo, router, searchParams],
  );

  const cerrarDetalle = useCallback(() => {
    const parametros = new URLSearchParams(searchParams.toString());
    parametros.delete(`${prefijo}detalle`);
    const query = parametros.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }, [pathname, prefijo, router, searchParams]);

  return { detalleId, abrirDetalle, cerrarDetalle };
}
