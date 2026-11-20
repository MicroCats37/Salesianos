/**
 * The state of the administration list of the videos.
 *
 * The default is the honest one and `cargando` is the state of a read that is
 * in flight: the route says it is working and it never invents a remaining
 * time.
 */
export type EstadoListaVideosAdmin =
  | "cargando"
  | "listo"
  | "error"
  | "sin-permiso";
