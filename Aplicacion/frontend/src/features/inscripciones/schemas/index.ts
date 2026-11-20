export {
  type Beneficio,
  type CatalogoDisciplinas,
  type CatalogoPaquetes,
  type Disciplina,
  type Paquete,
  type Precio,
  beneficioSchema,
  catalogoDisciplinasSchema,
  catalogoPaquetesSchema,
  disciplinaSchema,
  paqueteSchema,
  precioSchema,
} from "./catalogo.schema";
export {
  type CompraCreada,
  type ComprarCuposIn,
  compraCreadaSchema,
  comprarCuposInSchema,
} from "./compra-cupos.schema";
export {
  type AltaInscripcionFormData,
  type EquipoAltaFormData,
  AltaInscripcionSchema,
  EquipoAltaSchema,
} from "./alta-inscripcion.schema";
export {
  type Compra,
  type Equipo,
  type EquipoIn,
  type InscripcionDetalle,
  type InscripcionInicial,
  type InscripcionInicialIn,
  compraSchema,
  equipoInSchema,
  equipoSchema,
  equiposInscripcionSchema,
  inscripcionDetalleSchema,
  inscripcionInicialInSchema,
  inscripcionInicialSchema,
} from "./inscripcion.schema";
export {
  type Impedimento,
  type Participacion,
  type ParticipanteAsignarIn,
  type Pool,
  impedimentoSchema,
  participanteAsignarInSchema,
  participacionSchema,
  poolSchema,
} from "./pool.schema";
export {
  FormularioParticipanteSchema,
  type FormularioParticipanteFormData,
  ROLES_PARTICIPANTE,
  TIPOS_DOCUMENTO,
} from "./participante.schema";
