"use client";

import { handleApiError } from "@/errors";
import { useVideosLista } from "../hooks";
import type { EstadoVistaVideos } from "../types/video.types";
import { VideosListaView } from "./VideosListaView";

/**
 * The container of `VID-01`.
 *
 * The page (`src/app/(public)/videos/page.tsx`) is ROUTING-ONLY: this
 * container owns the read of the gallery and the VIEW owns the drawing.
 *
 * The gallery is PUBLIC: the route is anonymous and the answer of the server
 * is the one that is shown, without an invitation and without a session.
 */
export function VideosListaRuta() {
  const videos = useVideosLista();

  const error = videos.error ? handleApiError(videos.error) : null;

  const estado: EstadoVistaVideos = videos.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : videos.data
        ? "listo"
        : "sin-datos";

  return (
    <VideosListaView
      estado={estado}
      videos={videos.data}
      mensajeError={error?.message}
      reintentar={() => void videos.refetch()}
    />
  );
}
