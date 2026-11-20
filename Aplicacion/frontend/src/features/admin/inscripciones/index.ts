export type {
  AdminInscripcionDetalleOut,
  AdminInscripcionListItemOut,
  CompraDeCuposOut,
  CuposInscripcionOut,
  EquipoDeInscripcionOut,
  EventoDeHistorialOut,
  ParticipacionPoolOut,
  ParticipanteDeEquipoOut,
  PersonaAdminOut,
  PoolDeInscripcionOut,
  EstadoDetalleInscripcionAdmin,
  EstadoListaInscripcionesAdmin,
} from "./types/inscripciones-admin.types";
export {
  useDetalleInscripcionAdmin,
  useListaInscripcionesAdmin,
  useRetirarParticipanteAdmin,
} from "./hooks/useInscripcionesAdmin";
export {
  InscripcionAdminDetalleRuta,
  InscripcionAdminDetalleView,
  InscripcionesAdminRuta,
  InscripcionesAdminView,
} from "./views";
