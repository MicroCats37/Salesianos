export {
  type AltaInscripcionFormData,
  AltaInscripcionSchema,
  type EquipoAltaFormData,
  EquipoAltaSchema,
} from "./alta-inscripcion.schema";
export {
  type Beneficio,
  beneficioSchema,
  type CatalogoCategorias,
  type CatalogoDisciplinas,
  type CatalogoPaquetes,
  type CatalogoPromociones,
  type Categoria,
  catalogoCategoriasSchema,
  catalogoDisciplinasSchema,
  catalogoPaquetesSchema,
  catalogoPromocionesSchema,
  categoriaSchema,
  type Disciplina,
  disciplinaSchema,
  type Paquete,
  type Precio,
  type Promocion,
  paqueteSchema,
  precioSchema,
  promocionSchema,
} from "./catalogo.schema";
export {
  type CompraCreada,
  type ComprarCuposIn,
  compraCreadaSchema,
  comprarCuposInSchema,
} from "./compra-cupos.schema";
export {
  type Cotizacion,
  type CotizacionIn,
  cotizacionInSchema,
  cotizacionOutSchema,
} from "./cotizacion.schema";
export {
  type Compra,
  compraSchema,
  type Equipo,
  type EquipoIn,
  equipoInSchema,
  equipoSchema,
  equiposInscripcionSchema,
  type InscripcionDetalle,
  type InscripcionInicial,
  type InscripcionInicialIn,
  inscripcionDetalleSchema,
  inscripcionInicialInSchema,
  inscripcionInicialSchema,
  type PromocionInscripcion,
  promocionInscripcionSchema,
  referenciaEquipoSchema,
} from "./inscripcion.schema";
export {
  type FormularioParticipanteFormData,
  FormularioParticipanteSchema,
  ROLES_PARTICIPANTE,
  TIPOS_DOCUMENTO,
} from "./participante.schema";
export {
  type Impedimento,
  impedimentoSchema,
  type Participacion,
  type ParticipanteAsignarIn,
  type Pool,
  participacionSchema,
  participanteAsignarInSchema,
  poolSchema,
} from "./pool.schema";
