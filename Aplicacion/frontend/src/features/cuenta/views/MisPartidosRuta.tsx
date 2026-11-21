"use client";

import { handleApiError } from "@/errors";
import { usePartidosCuenta } from "../hooks/usePartidosCuenta";
import { MisPartidosView } from "./MisPartidosView";

/**
 * The container of "MIS PARTIDOS".
 *
 * The page (`src/app/(cuenta)/mis-partidos/page.tsx`) is ROUTING-ONLY: this
 * container owns the read and the VIEW owns the drawing.
 *
 * The read is of the ACCOUNT: it needs a session and the identity is the
 * session's. The container never sends a person, a user or a team.
 */
export function MisPartidosRuta() {
  const partidos = usePartidosCuenta();

  const error = partidos.error ? handleApiError(partidos.error) : null;

  const estado = partidos.isPending
    ? "cargando"
    : error
      ? "error"
      : partidos.data
        ? "listo"
        : "sin-datos";

  return (
    <MisPartidosView
      estado={estado}
      partidos={partidos.data}
      mensajeError={error?.message}
      reintentar={() => void partidos.refetch()}
    />
  );
}
