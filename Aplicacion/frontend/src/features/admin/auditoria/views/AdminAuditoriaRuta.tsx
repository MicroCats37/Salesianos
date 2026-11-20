"use client";

import { useAuditoriaAdmin } from "../hooks/useAuditoriaAdmin";
import { AdminAuditoriaView } from "./AdminAuditoriaView";

export interface AdminAuditoriaRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * The container of the acta of the sensitive actions.
 *
 * The route of the acta does NOT exist yet (`RT-ADM-02`), so the state is
 * the honest one and the view says so.
 */
export function AdminAuditoriaRuta({ parametros }: AdminAuditoriaRutaProps) {
  const estado = useAuditoriaAdmin({
    edicion_id: parametros.edicion_id,
    accion: parametros.accion,
    page: parametros.page ? Number(parametros.page) : undefined,
    page_size: parametros.page_size ? Number(parametros.page_size) : undefined,
  });

  return <AdminAuditoriaView estado={estado} />;
}
