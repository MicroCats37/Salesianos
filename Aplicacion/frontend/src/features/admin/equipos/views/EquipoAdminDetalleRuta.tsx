"use client";

import { useDetalleEquipoAdmin } from "../hooks/useEquiposAdmin";
import { EquipoAdminDetalleView } from "./EquipoAdminDetalleView";

export interface EquipoAdminDetalleRutaProps {
  /** The identifier of the team, taken from the path. */
  id: string;
}

/**
 * ADM-08 - the container of `/administracion/equipos/{id}`.
 *
 * The route of the detail does NOT exist yet (`RT-IN-10`), so the state is the
 * honest one and the view says so.
 */
export function EquipoAdminDetalleRuta({ id }: EquipoAdminDetalleRutaProps) {
  const estado = useDetalleEquipoAdmin(id);

  return <EquipoAdminDetalleView id={id} estado={estado} />;
}
