import type { Method } from "axios";
import type { ZodType } from "zod";
import type {
  Video,
  VideoListItem,
} from "@/features/videos/schemas/video.schema";
import { apiSend } from "@/lib/api";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  adminVideoEnvelope,
  adminVideosEnvelope,
} from "../schemas/admin.video.schema";

/**
 * The ONE client of the administration of the videos.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/videos/presentation/controllers/admin_videos_controller.py`
 * → `AdminVideosController`): a route that is not registered does not exist
 * and is never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `GET /api/administracion/videos` | GET | `/administracion/videos` | `PaginatedData[VideoListOut]` |
 * | `GET /api/administracion/videos/{video_id}` | GET | `/administracion/videos/{video_id}` | `VideoOut` |
 * | `POST /api/administracion/videos` | POST | `/administracion/videos` | `VideoOut` |
 * | `PATCH /api/administracion/videos/{video_id}` | PATCH | `/administracion/videos/{video_id}` | `VideoOut` |
 * | `DELETE /api/administracion/videos/{video_id}` | DELETE | `/administracion/videos/{video_id}` | `204` sin cuerpo |
 *
 * The gate is `RequireAdmin` (`is_staff` OR `is_superuser`): the backend
 * evaluates it on EVERY request. Hiding the button is a courtesy; the `403`
 * of the backend is the control.
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 */

/** The base of every route of the administration of the videos. */
const BASE = "/administracion/videos";

/** The route of the administration of the videos. */
export function rutaVideosAdmin(): string {
  return BASE;
}

/** The route of ONE video of the administration. */
export function rutaVideoAdmin(id: string): string {
  return `${BASE}/${encodeURIComponent(id)}`;
}

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is NOT a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY, so this error never
 * hides behind a partial trust.
 */
export class ErrorContratoAdminVideo extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoAdminVideo";
  }
}

/**
 * The answer of the server, with the message that the controller declares.
 *
 * The message travels VERBATIM to the toast: the interface never rewrites
 * the wording the server chose (`contract/api-wrapper-presenter-contract.md`
 * §8).
 */
export interface RespuestaAdminVideo<T> {
  /** The payload of the answer. */
  data: T;
  /** The public message of the controller, when it declares one. */
  message: string | null;
}

/**
 * Reads the message of the envelope.
 *
 * It is read from the RAW body and never invented: the controller declares it
 * when it declares it, and the envelope always carries the key.
 */
function leerMensaje(body: unknown): string | null {
  if (typeof body !== "object" || body === null) return null;

  const mensaje = (body as { message?: unknown }).message;

  return typeof mensaje === "string" ? mensaje : null;
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
  payload?: unknown,
  params?: Record<string, string | number | undefined>,
): Promise<RespuestaAdminVideo<T>> {
  const { status, data } = await apiSend<unknown>(method, url, payload, {
    params,
  });

  if (status === 204 || data === null) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new ErrorContratoAdminVideo(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const parseado = envelope.safeParse(data);

  if (!parseado.success) {
    throw new ErrorContratoAdminVideo(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.error,
    );
  }

  if (!parseado.data.success || parseado.data.data === null) {
    throw new ErrorContratoAdminVideo("El servidor respondió sin datos.");
  }

  return {
    data: parseado.data.data,
    message: leerMensaje(data),
  };
}

/** The list of the videos of the administration (`GET /administracion/videos`). */
export async function listarVideosAdmin(params?: {
  q?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResult<VideoListItem>> {
  const respuesta = await pedir(
    "get",
    BASE,
    adminVideosEnvelope,
    undefined,
    params,
  );

  return respuesta.data;
}

/** The detail of a video (`GET /administracion/videos/{video_id}`). */
export async function obtenerVideoAdmin(id: string): Promise<Video> {
  const respuesta = await pedir(
    "get",
    `${BASE}/${encodeURIComponent(id)}`,
    adminVideoEnvelope,
  );

  return respuesta.data;
}

/** The publication of a video (`POST /administracion/videos`). */
export function crearVideoAdmin(
  payload: unknown,
): Promise<RespuestaAdminVideo<Video>> {
  return pedir("post", BASE, adminVideoEnvelope, payload);
}

/**
 * The edition of a video (`PATCH /administracion/videos/{video_id}`).
 *
 * The `PATCH` is PARTIAL: only the fields that the operator touched travel,
 * and the payload that leaves here is the one the `update` mode of the form
 * built.
 */
export function actualizarVideoAdmin(
  id: string,
  payload: unknown,
): Promise<RespuestaAdminVideo<Video>> {
  return pedir(
    "patch",
    `${BASE}/${encodeURIComponent(id)}`,
    adminVideoEnvelope,
    payload,
  );
}

/**
 * The deletion of a video (`DELETE /administracion/videos/{video_id}`).
 *
 * The answer is a `204` WITHOUT BODY: it is never parsed. A video that does
 * not exist answers a `404` that the transport turns into an error.
 */
export async function eliminarVideoAdmin(id: string): Promise<void> {
  const { status } = await apiSend<unknown>(
    "delete",
    `${BASE}/${encodeURIComponent(id)}`,
  );

  if (status !== 204) {
    throw new ErrorContratoAdminVideo(
      "El servidor respondió con un cuerpo donde se esperaba una respuesta vacía.",
    );
  }
}
