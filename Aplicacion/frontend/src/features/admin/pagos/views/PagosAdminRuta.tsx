"use client";

import { useListaPagosAdmin } from "../hooks/usePagosAdmin";
import { PagosAdminView } from "./PagosAdminView";

export interface PagosAdminRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * ADM-14 - the container of `/administracion/pagos`.
 *
 * The route of the operational list does NOT exist yet (`RT-PG-04`), so the
 * state is the honest one and the view says so.
 */
export function PagosAdminRuta({ parametros }: PagosAdminRutaProps) {
  const estado = useListaPagosAdmin(parametros);

  return <PagosAdminView parametros={parametros} estado={estado} />;
}
