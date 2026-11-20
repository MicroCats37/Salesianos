export type {
  AdminEquipoDetalleOut,
  AdminEquipoListItemOut,
  CandidatoAEquipoOut,
  EquipoOperativoOut,
  ParticipanteDeEquipoOut,
  PlantillaEquipoOut,
  EstadoDetalleEquipoAdmin,
  EstadoListaEquiposAdmin,
} from "./types/equipos-admin.types";
export {
  useDetalleEquipoAdmin,
  useListaEquiposAdmin,
} from "./hooks/useEquiposAdmin";
export {
  EquipoAdminDetalleRuta,
  EquipoAdminDetalleView,
  EquiposAdminRuta,
  EquiposAdminView,
} from "./views";
