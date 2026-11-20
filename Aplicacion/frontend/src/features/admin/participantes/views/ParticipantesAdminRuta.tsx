"use client";

import { useListaParticipantesAdmin } from "../hooks/useParticipantesAdmin";
import { ParticipantesAdminView } from "./ParticipantesAdminView";

export interface ParticipantesAdminRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/**
 * ADM-09 - the container of `/administracion/participantes`.
 *
 * The route of the search does NOT exist yet (`RT-IN-11`), so the state is the
 * honest one and the view keeps its prompt.
 */
export function ParticipantesAdminRuta({
  parametros,
}: ParticipantesAdminRutaProps) {
  const estado = useListaParticipantesAdmin(parametros);

  return <ParticipantesAdminView parametros={parametros} estado={estado} />;
}
