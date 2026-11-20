export {
  obtenerCatalogoCategorias,
  obtenerCatalogoDisciplinas,
  obtenerCatalogoPaquetes,
  obtenerCatalogoPromociones,
  RUTA_CATALOGO_CATEGORIAS,
  RUTA_CATALOGO_DISCIPLINAS,
  RUTA_CATALOGO_PAQUETES,
  RUTA_CATALOGO_PROMOCIONES,
} from "./catalogo.service";
export { cotizarPaquete, RUTA_COTIZACIONES } from "./cotizacion.service";
export {
  agregarParticipante,
  comprarCupos,
  crearInscripcionInicial,
  obtenerInscripcion,
  obtenerPool,
  RUTA_INSCRIPCIONES,
  retirarParticipante,
} from "./inscripcion.service";
export type { Respuesta } from "./respuesta.service";
export { leerRespuesta } from "./respuesta.service";
