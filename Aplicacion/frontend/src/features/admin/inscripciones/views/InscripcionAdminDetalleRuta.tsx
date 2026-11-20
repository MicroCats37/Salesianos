"use client";

import { useDetalleInscripcionAdmin } from "../hooks/useInscripcionesAdmin";
import { InscripcionAdminDetalleView } from "./InscripcionAdminDetalleView";

export interface InscripcionAdminDetalleRutaProps {
  /** The identifier of the registration, taken from the path. */
  id: string;
}

/**
 * ADM-06 - the container of `/administracion/inscripciones/{id}`.
 *
 * The route of the detail does NOT exist yet (`RT-IN-08`), so the state is the
 * honest one and the view says so.
 */
export function InscripcionAdminDetalleRuta({
  id,
}: InscripcionAdminDetalleRutaProps) {
  const estado = useDetalleInscripcionAdmin(id);

  return <InscripcionAdminDetalleView id={id} estado={estado} />;
}
