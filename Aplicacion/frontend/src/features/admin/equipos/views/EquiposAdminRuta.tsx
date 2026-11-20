"use client";

import { useListaEquiposAdmin } from "../hooks/useEquiposAdmin";
import { EquiposAdminView } from "./EquiposAdminView";

export interface EquiposAdminRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * ADM-07 - the container of `/administracion/equipos`.
 *
 * The route of the list does NOT exist yet (`RT-IN-09`), so the state is the
 * honest one and the view says so.
 */
export function EquiposAdminRuta({ parametros }: EquiposAdminRutaProps) {
  const estado = useListaEquiposAdmin(parametros);

  return <EquiposAdminView parametros={parametros} estado={estado} />;
}
