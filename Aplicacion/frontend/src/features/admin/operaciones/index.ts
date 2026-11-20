export {
  BarraFiltros,
  BusquedaOperativa,
  CifrasCupos,
  ConfirmacionIrreversible,
  EsqueletoOperativo,
  ExplicacionVeredicto,
  ListaOperativa,
  MarcoOperativo,
  PaginacionOperativa,
  VeredictoConCausa,
  VeredictoOperativo,
} from "./components";
export type {
  AccionOperativa,
  ColumnaOperativa,
  CuposOperativosOut,
  EstadoDeclarado,
  EstadoSuperficie,
  FilaOperativa,
  FiltroOperativo,
  OpcionFiltro,
  PaginaOperativa,
  PrioridadColumna,
  RolOperativo,
  Veredicto,
} from "./types/operaciones.types";
  export {
    CODIGOS_ESTADO_OPERATIVO_PAGO,
    rolOperativoDesdeCodigo,
    veredictoDesdeEstadoOperativo,
  } from "./utils/veredicto.adapter";
