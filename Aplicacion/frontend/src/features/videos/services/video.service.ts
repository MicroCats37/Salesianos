import type { Method } from "axios";
import type { ZodType } from "zod";
import { apiSend } from "@/lib/api";
import {
  type Video,
  type VideoListItem,
  videoEnvelope,
  videosEnvelope,
} from "../schemas/video.schema";

/**
 * The ONE client of the public gallery of videos.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/videos/presentation/controllers/videos_controller.py`
 * → `VideoController`): a route that is not registered does not exist and is
 * never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `GET /api/videos` | GET | `/videos` | `list[VideoListOut]` |
 * | `GET /api/videos/{video_id}` | GET | `/videos/{video_id}` | `VideoOut` |
 *
 * The public surface exposes NO writes: a video is published from the panel of
 * administration (`AdminVideosController`).
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 */

/** The base of every route of the gallery. */
const BASE = "/videos";

/** The route of the public gallery of videos. */
export function rutaVideos(): string {
  return BASE;
}

/** The route of ONE video. */
export function rutaVideo(id: string): string {
  return `${BASE}/${encodeURIComponent(id)}`;
}

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is NOT a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY, so this error never
 * hides behind a partial trust.
 */
export class ErrorContratoVideo extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoVideo";
  }
}

/**
 * The single way this feature talks to the backend.
 *
 * It applies the rules of the envelope ONCE: the `204` is never parsed, the
 * body is parsed with the Zod mirror of the wrapper and a body that does not
 * comply is a loud failure.
 */
async function pedir<T>(
  method: Method,
  url: string,
  envelope: ZodType<{ success: boolean; data: T | null }>,
  params?: Record<string, string | number | undefined>,
): Promise<T> {
  const { status, data } = await apiSend<unknown>(method, url, undefined, {
    params,
  });

  if (status === 204 || data === null) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new ErrorContratoVideo(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const parseado = envelope.safeParse(data);

  if (!parseado.success) {
    throw new ErrorContratoVideo(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.error,
    );
  }

  if (!parseado.data.success || parseado.data.data === null) {
    throw new ErrorContratoVideo("El servidor respondió sin datos.");
  }

  return parseado.data.data;
}

/**
 * The public gallery (`GET /api/videos`).
 *
 * The list is NOT paginated: it is the whole gallery, from the newest video
 * to the oldest one.
 */
export function listarVideos(): Promise<VideoListItem[]> {
  return pedir("get", BASE, videosEnvelope);
}

/** The detail of a video (`GET /api/videos/{video_id}`). */
export function obtenerVideo(id: string): Promise<Video> {
  return pedir("get", `${BASE}/${encodeURIComponent(id)}`, videoEnvelope);
}
