/**
 * Public surface of the administration feature.
 *
 * Only the UI components are exposed here; the schemas, services and hooks
 * are imported from their own folders (`contract/next-app-architecture-contract.md`
 * §7).
 */
export {
  AdminAccessDenied,
  type AdminAccessDeniedProps,
  AdminAcreditacionesLista,
  AdminAlertList,
  type AdminAlertListProps,
  type AdminColumna,
  AdminEquiposLista,
  AdminEstadoBadge,
  type AdminEstadoBadgeProps,
  type AdminFiltroOpcion,
  AdminFiltroRangoFechas,
  AdminFiltroSelect,
  AdminFiltrosSheet,
  type AdminFiltrosSheetProps,
  AdminInscripcionDetalle,
  type AdminInscripcionDetalleProps,
  AdminInscripcionesLista,
  AdminKpiCard,
  type AdminKpiCardProps,
  AdminListaError,
  AdminListaOperativa,
  AdminListaSkeleton,
  AdminListaToolbar,
  AdminListaVacia,
  AdminOverview,
  AdminPageHeader,
  type AdminPageHeaderProps,
  AdminPagosLista,
  AdminParticipantesLista,
  AdminSeccionNav,
  AdminShell,
  AdminUsuariosLista,
} from "./components";

export {
  useAdminAccesos,
  useAdminAcreditacionDetalle,
  useAdminAcreditaciones,
  useAdminCatalogos,
  useAdminControlLista,
  useAdminDetalleUrl,
  useAdminEquipos,
  useAdminInscripcionDetalle,
  useAdminInscripciones,
  useAdminListaUrl,
  useAdminPagoDetalle,
  useAdminPagos,
  useAdminParticipaciones,
  useAdminParticipantes,
  useAdminResumen,
  useAdminSession,
  useAdminUsuarioDetalle,
  useAdminUsuarios,
  useEsAdmin,
} from "./hooks";

export type {
  AdminAcreditacionDetail,
  AdminCatalogosResponse,
  AdminInscripcionDetail,
  AdminMeResponse,
  AdminPagoDetail,
  AdminResumenResponse,
  AdminUsuarioDetail,
} from "./schemas";

export type {
  AdminAlertGroup,
  AdminAlertItem,
  AdminEstadoLista,
  AdminKpi,
  AdminTone,
} from "./utils";
