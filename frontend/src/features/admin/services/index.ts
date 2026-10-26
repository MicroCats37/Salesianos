export {
  type AdminSession,
  type AdminSessionStatus,
  revalidateAdminSession,
} from "./admin.guard.service";
export { adminGet } from "./admin.http.service";
export {
  getAdminInscripcionDetalle,
  getAdminInscripciones,
} from "./admin.inscripcion.service";
export { getAdminMe } from "./admin.me.service";
export {
  getAdminAccesos,
  getAdminAcreditacionDetalle,
  getAdminAcreditaciones,
  getAdminEquipos,
  getAdminParticipaciones,
  getAdminParticipantes,
} from "./admin.operacion.service";
export {
  getAdminPagoDetalle,
  getAdminPagos,
} from "./admin.pago.service";
export {
  getAdminCatalogos,
  getAdminResumen,
} from "./admin.resumen.service";
export {
  getAdminUsuarioDetalle,
  getAdminUsuarios,
} from "./admin.usuario.service";
