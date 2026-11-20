"use client";

import { videoClaves } from "@/features/videos/utils/video.claves.utils";
import { useApiCreate, useApiDelete, useApiQuery, useApiUpdate } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type { ActualizarVideoFormData } from "../schemas/admin.video.schema";
import {
  adminVideoEnvelope,
  adminVideosEnvelope,
} from "../schemas/admin.video.schema";
import { rutaVideosAdmin } from "../services/admin.video.service";

/**
 * The reads and the writes of the administration of the videos.
 *
 * Every mutation declares the reads it dirties, and the invalidation lives
 * INSIDE the mutation (not in `onSettled`): a component that unmounts
 * while the mutation is in flight would never invalidate, and the cache
 * would keep the answer that the server already changed.
 *
 * The invalidation target is the WHOLE namespace of the videos: publishing a
 * video changes the public gallery AND the administration list, and the two
 * must never disagree.
 */

/** The parameters that change the answer of the administration list. */
export type ParamsListaVideosAdmin = {
  /** The search by title or description. */
  q?: string;
  /** The order: `created_at`, `updated_at` or `titulo`. */
  ordering?: string;
  /** The page, 1-based. */
  page?: number;
  /** The size of the page. */
  page_size?: number;
};

/**
 * The list of the videos of the administration
 * (`GET /administracion/videos`).
 *
 * It is an administrative list: it changes with the second, so the read stays
 * fresh for a short window.
 */
export function useListaVideosAdmin(params?: ParamsListaVideosAdmin) {
  return useApiQuery({
    queryKey: videoClaves.adminLista(),
    url: rutaVideosAdmin(),
    schema: datosDelEnvelope(adminVideosEnvelope),
    params,
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}

/**
 * The publication of a video (`POST /administracion/videos`).
 *
 * The payload is built by the hook and never in the form: the transport owns
 * the construction of the body (`buildApiPayload`) and the form owns the
 * layout.
 */
export function useCrearVideoAdmin() {
  return useApiCreate({
    url: rutaVideosAdmin(),
    schema: datosDelEnvelope(adminVideoEnvelope),
    invalidateKeys: [videoClaves.todas],
  });
}

/** The arguments of the edition of a video. */
export interface EditarVideoArgs {
  /** The identifier of the video that is edited. */
  id: string;
  /** The fields that the operator touched. */
  datos: ActualizarVideoFormData;
}

/**
 * The edition of a video (`PATCH /administracion/videos/{video_id}`).
 *
 * The `PATCH` is partial: the payload carries only the fields that changed.
 */
export function useActualizarVideoAdmin() {
  const mutacion = useApiUpdate({
    baseUrl: rutaVideosAdmin(),
    method: "PATCH",
    schema: datosDelEnvelope(adminVideoEnvelope),
    invalidateKeys: [videoClaves.todas],
  });

  return {
    ...mutacion,
    mutateAsync: (args: EditarVideoArgs) =>
      mutacion.mutateAsync({ id: args.id, data: args.datos }),
  };
}

/**
 * The deletion of a video (`DELETE /administracion/videos/{video_id}`).
 *
 * The answer is a `204` without body, so there is NO message of the server to
 * show: the confirmation is the fact that the row is gone from the table.
 */
export function useEliminarVideoAdmin() {
  return useApiDelete({
    baseUrl: rutaVideosAdmin(),
    showSuccessToast: false,
    invalidateKeys: [videoClaves.todas],
  });
}
