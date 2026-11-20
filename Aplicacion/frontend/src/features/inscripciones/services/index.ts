export {
  RUTA_CATALOGO_DISCIPLINAS,
  RUTA_CATALOGO_PAQUETES,
  obtenerCatalogoDisciplinas,
  obtenerCatalogoPaquetes,
} from "./catalogo.service";
export {
  RUTA_INSCRIPCIONES,
  agregarParticipante,
  comprarCupos,
  crearInscripcionInicial,
  obtenerInscripcion,
  obtenerPool,
  retirarParticipante,
} from "./inscripcion.service";
export type { Respuesta } from "./respuesta.service";
export { leerRespuesta } from "./respuesta.service";
