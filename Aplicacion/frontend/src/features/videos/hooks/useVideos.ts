"use client";

import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { videoEnvelope, videosEnvelope } from "../schemas/video.schema";
import { rutaVideo, rutaVideos } from "../services/video.service";
import { videoClaves } from "../utils/video.claves.utils";

/**
 * The public gallery of videos (`GET /videos`).
 *
 * It is a CATALOGUE: the videos change with the edition, not with the second,
 * so the read stays fresh for the whole window of the catalogue.
 */
export function useVideosLista() {
  return useApiQuery({
    queryKey: videoClaves.lista(),
    url: rutaVideos(),
    schema: datosDelEnvelope(videosEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}

/**
 * The detail of a video (`GET /videos/{video_id}`).
 *
 * The identifier is the identity of the video in the URL. The read is DISABLED
 * when there is no identifier: the frontend never calls a route it cannot open.
 */
export function useVideoDetalle(id: string | undefined) {
  return useApiQuery({
    queryKey: videoClaves.detalle(id ?? ""),
    url: id ? rutaVideo(id) : null,
    schema: datosDelEnvelope(videoEnvelope),
    queryOptions: {
      enabled: Boolean(id),
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}
