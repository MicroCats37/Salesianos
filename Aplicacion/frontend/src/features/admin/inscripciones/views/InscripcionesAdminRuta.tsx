"use client";

import { useListaInscripcionesAdmin } from "../hooks/useInscripcionesAdmin";
import { InscripcionesAdminView } from "./InscripcionesAdminView";

export interface InscripcionesAdminRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * ADM-05 - the container of `/administracion/inscripciones`.
 *
 * The page reads the query string and hands it over; THIS container reads the
 * data and hands the STATE to the view. The page stays a routing file and the
 * view stays a presentation file (`salesianos-feature-architecture`).
 *
 * The route of the list does NOT exist yet (`RT-IN-07`), so the state is the
 * honest one and the view says so.
 */
export function InscripcionesAdminRuta({
  parametros,
}: InscripcionesAdminRutaProps) {
  const estado = useListaInscripcionesAdmin(parametros);

  return <InscripcionesAdminView parametros={parametros} estado={estado} />;
}
