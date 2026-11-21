"use client";

import { handleApiError } from "@/errors";
import { useEncuentrosPublicos } from "../hooks/useEncuentrosPublicos";
import { useEncuentrosPublicosRealtime } from "../hooks/useEncuentrosPublicosRealtime";
import {
  EncuentrosPublicosView,
  type EstadoVistaEncuentrosPublicos,
} from "./EncuentrosPublicosView";

/**
 * The container of the public page of the matches.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * The page (`src/app/(public)/partidos/page.tsx`) is ROUTING-ONLY: this
 * container owns the read and the VIEW owns the drawing.
 *
 * The route is PUBLIC: the answer of the server is the one that is shown,
 * without an invitation and without a session.
 */
export function EncuentrosPublicosRuta() {
  const encuentros = useEncuentrosPublicos();
  useEncuentrosPublicosRealtime();

  const error = encuentros.error ? handleApiError(encuentros.error) : null;

  const estado: EstadoVistaEncuentrosPublicos = encuentros.isPending
    ? "cargando"
    : error
      ? "error"
      : encuentros.data
        ? "listo"
        : "sin-datos";

  return (
    <EncuentrosPublicosView
      estado={estado}
      encuentros={encuentros.data}
      mensajeError={error?.message}
      reintentar={() => void encuentros.refetch()}
    />
  );
}
