/**
 * The TRANSVERSAL summary of the administration area (`ADM-01`).
 *
 * It is ONE dataset (`admin.resumen`) with ONE service, ONE hook and ONE
 * namespace: the area never has two clients of the same data
 * (`FND-08` §3 regla 1).
 */
export { useResumenAdmin } from "./hooks/useResumenAdmin";
export {
  resumenAccionSchema,
  resumenIncidenciaSchema,
  resumenMetricaSchema,
  resumenOperativoEnvelope,
  resumenOperativoSchema,
} from "./schemas/resumen-admin.schema";
export { obtenerResumenAdmin } from "./services/resumen-admin.service";
export type {
  EstadoResumenAdmin,
  ResumenAccion,
  ResumenIncidencia,
  ResumenMetrica,
  ResumenOperativo,
} from "./types/resumen-admin.types";
export { AdminResumenRuta } from "./views/AdminResumenRuta";
export { AdminResumenView } from "./views/AdminResumenView";
