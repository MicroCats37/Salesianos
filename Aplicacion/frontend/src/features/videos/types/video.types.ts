import type { Video, VideoListItem } from "../schemas/video.schema";

export type { Video, VideoListItem };

/**
 * The state a route is in.
 *
 * The default is the honest one and `cargando` is the state of a read that is
 * in flight: the route says it is working and it never invents a remaining
 * time.
 */
export type EstadoVistaVideos =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";
