"use client";

import { handleApiError } from "@/errors";
import { useVideoDetalle } from "../hooks";
import type { EstadoVistaVideos } from "../types/video.types";
import { VideoDetalleView } from "./VideoDetalleView";

export interface VideoDetalleRutaProps {
  /** The identifier of the video, the identity in the URL. */
  id: string;
}

/**
 * The container of `VID-02`.
 *
 * The page (`src/app/(public)/videos/[id]/page.tsx`) is ROUTING-ONLY: this
 * container owns the read of the video and the VIEW owns the drawing.
 *
 * The route is PUBLIC: the video is a public content by definition, so the
 * visitor reaches it without a session.
 */
export function VideoDetalleRuta({ id }: VideoDetalleRutaProps) {
  const consulta = useVideoDetalle(id);

  const error = consulta.error ? handleApiError(consulta.error) : null;

  const estado: EstadoVistaVideos = consulta.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : consulta.data
        ? "listo"
        : "sin-datos";

  return (
    <VideoDetalleView
      estado={estado}
      video={consulta.data}
      mensajeError={error?.message}
      reintentar={() => void consulta.refetch()}
    />
  );
}
