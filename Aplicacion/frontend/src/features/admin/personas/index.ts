/**
 * The administrative search of PEOPLE (`RT-ID-07` · `RT-ID-08`).
 *
 * It is ONE dataset (`admin.personas`) with ONE service, ONE hook and ONE
 * namespace: the area never has two clients of the same data
 * (`FND-08` §3 regla 1).
 */
export { usePersonasAdmin } from "./hooks/usePersonasAdmin";
export {
  adminPersonaDetalleEnvelope,
  adminPersonaDetalleSchema,
  adminPersonaListItemSchema,
  listaPersonasAdminEnvelope,
} from "./schemas/persona-admin.schema";
export {
  listarPersonasAdmin,
  obtenerPersonaAdmin,
} from "./services/persona-admin.service";
export type {
  AdminPersonaDetalleOut,
  AdminPersonaListItemOut,
  EstadoPersonasAdmin,
} from "./types/personas-admin.types";
