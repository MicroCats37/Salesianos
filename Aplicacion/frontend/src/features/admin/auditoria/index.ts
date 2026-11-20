/**
 * The ACTA of the sensitive actions of the administration area (`ADM-15`).
 *
 * It is ONE dataset (`admin.auditoria`) with ONE service, ONE hook and ONE
 * namespace: the area never has two clients of the same data
 * (`FND-08` §3 regla 1).
 */
export { useAuditoriaAdmin } from "./hooks/useAuditoriaAdmin";
export {
  auditoriaItemSchema,
  auditoriaListadoEnvelope,
  auditoriaListadoSchema,
} from "./schemas/auditoria-admin.schema";
export {
  listarAuditoriaAdmin,
  obtenerAuditoriaAdmin,
} from "./services/auditoria-admin.service";
export type {
  AuditoriaItemOut,
  AuditoriaListadoOut,
  EstadoAuditoriaAdmin,
} from "./types/auditoria-admin.types";
export { AdminAuditoriaRuta } from "./views/AdminAuditoriaRuta";
export { AdminAuditoriaView } from "./views/AdminAuditoriaView";
