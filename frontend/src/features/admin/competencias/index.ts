/**
 * Public surface of the `competencias` feature of the administration area.
 *
 * Only the UI components are exposed here; the schemas, the services and the
 * hooks are imported from their own folders
 * (`contract/next-app-architecture-contract.md` §7).
 */
export {
  CompetenciaErrorAlert,
  type CompetenciaErrorAlertProps,
  CompetenciasAccionesEncuentro,
  CompetenciasAgenda,
  CompetenciasCuadro,
  CompetenciasDetalle,
  type CompetenciasDetalleProps,
  CompetenciasEditores,
  type CompetenciasEditoresProps,
  CompetenciasEnlaceCuadro,
  CompetenciasFiltros,
  type CompetenciasFiltrosProps,
  CompetenciasLista,
  CompetenciasSubnav,
} from "./components";
