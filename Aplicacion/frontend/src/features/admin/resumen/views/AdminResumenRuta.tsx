"use client";

import { useResumenAdmin } from "../hooks/useResumenAdmin";
import { AdminResumenView } from "./AdminResumenView";

export interface AdminResumenRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * ADM-01: the container of `/administracion`.
 *
 * The route of the transversal summary does NOT exist yet (`RT-ADM-01`), so
 * the state is the honest one and the view says so.
 */
export function AdminResumenRuta({ parametros }: AdminResumenRutaProps) {
  const estado = useResumenAdmin(parametros.edicion_id);

  return <AdminResumenView estado={estado} />;
}
