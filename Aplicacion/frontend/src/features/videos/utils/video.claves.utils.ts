import type { QueryKey } from "@tanstack/react-query";
import { buildQueryKey } from "@/shared/utils/query-keys";

/**
 * The query keys of the videos.
 *
 * They live HERE and nowhere else: a component never spells a key. ONE
 * dataset, ONE namespace: every read of the gallery and every read of the
 * administration list of videos shares `["videos", …]`, and the invalidation
 * of a mutation that publishes a video dirties the whole namespace.
 *
 * EVERY parameter that changes the answer travels in the key (the search, the
 * order and the page). A parameter that is `undefined` is dropped, so
 * `{ page: undefined }` and no parameters at all are the SAME cache entry.
 */

/** The root of the videos namespace. */
const VIDEOS: QueryKey = ["videos"];

export const videoClaves = {
  /** The root of the whole namespace: the invalidation target. */
  todas: ["videos"] as const,

  /** The public gallery (`GET /api/videos`). */
  lista: () => [...VIDEOS, "lista"] as const,

  /** The detail of ONE video (`GET /api/videos/{video_id}`). */
  detalle: (id: string) => [...VIDEOS, "detalle", id] as const,

  /**
   * ONE page of the administration list
   * (`GET /api/administracion/videos`).
   *
   * The search, the order and the page travel in it: two pages are two cache
   * entries.
   */
  adminLista: (params?: {
    q?: string;
    ordering?: string;
    page?: number;
    page_size?: number;
  }) => buildQueryKey([...VIDEOS, "admin", "lista"], params),

  /** The administration detail of ONE video. */
  adminDetalle: (id: string) => [...VIDEOS, "admin", "detalle", id] as const,
} as const;
