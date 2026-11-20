import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirror of the wrappers of the videos.
 *
 * The mirror is 1:1 with the backend (`modules/videos/presentation/schemas/videos_schemas.py`):
 * `VideoListOut` is `{id, titulo, descripcion, url, created_at}` and `VideoOut`
 * adds `updated_at`. There is NO `z.any()`: a body that does not comply is a
 * loud failure, never a partially trusted value.
 */

/** An identifier of the domain: a UUID published by the presenter. */
const id = z.string().uuid();

/** An instant published by the presenter. */
const marcaTiempo = z.string().min(1);

/** A video of the public gallery (`VideoListOut`). */
export const videoListItemSchema = z.object({
  id,
  titulo: z.string(),
  descripcion: z.string(),
  url: z.string(),
  created_at: marcaTiempo,
});

/** The detail of a video (`VideoOut`). */
export const videoSchema = videoListItemSchema.extend({
  updated_at: marcaTiempo,
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The public gallery (`GET /api/videos`). */
export const videosEnvelope = apiResponseSchema(z.array(videoListItemSchema));

/** The detail of a video (`GET /api/videos/{video_id}`). */
export const videoEnvelope = apiResponseSchema(videoSchema);

export type VideoListItem = z.infer<typeof videoListItemSchema>;
export type Video = z.infer<typeof videoSchema>;
