/**
 * State vocabularies of the administration area — the CLIENT mirror of the
 * `TextChoices` of the owning modules.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically (same
 * pattern as `features/inscripciones/utils/pool.estado.ts`). That is also why
 * it declares NO relative import: a leaf module is the only kind Node can
 * load while it strips the types.
 *
 * The vocabularies are the ones of the backend:
 * `modules.salesianos_fest.domain.constants`, `modules.commerce.domain.constants`
 * and `modules.pagos.domain.constants`.
 *
 * A state the UI does not know about is rendered NEUTRALLY (`slate`) and
 * keeps its raw value: the UI never invents a semantic it was not told.
 *
 * The states of the REGISTRATION live in `admin.resumen.utils.ts` (the
 * overview owns them) and are re-exported by the barrel of this folder.
 */

/** Visual tone of a KPI tile, an alert item or a state badge. */
export type AdminTone =
  | "brand"
  | "emerald"
  | "cyan"
  | "violet"
  | "orange"
  | "amber"
  | "rose"
  | "red"
  | "blue"
  | "slate";

const ESTADO_COMPRA_TONE: Record<string, AdminTone> = {
  PENDIENTE: "amber",
  PAGADA: "emerald",
  CANCELADA: "rose",
};

const ESTADO_COMPRA_LABEL: Record<string, string> = {
  PENDIENTE: "Pendiente",
  PAGADA: "Pagada",
  CANCELADA: "Cancelada",
};

const ESTADO_ORDEN_TONE: Record<string, AdminTone> = {
  PENDIENTE: "amber",
  PAGADA: "emerald",
  CANCELADA: "rose",
  VENCIDA: "red",
};

const ESTADO_ORDEN_LABEL: Record<string, string> = {
  PENDIENTE: "Pendiente",
  PAGADA: "Pagada",
  CANCELADA: "Cancelada",
  VENCIDA: "Vencida",
};

const ESTADO_EQUIPO_TONE: Record<string, AdminTone> = {
  EQUIPO_ACTIVO: "emerald",
  EQUIPO_CANCELADO: "slate",
};

const ESTADO_EQUIPO_LABEL: Record<string, string> = {
  EQUIPO_ACTIVO: "Activo",
  EQUIPO_CANCELADO: "Cancelado",
};

const ROSTER_TONE: Record<string, AdminTone> = {
  COMPLETO: "emerald",
  INCOMPLETO: "amber",
};

const ROSTER_LABEL: Record<string, string> = {
  COMPLETO: "Completo",
  INCOMPLETO: "Incompleto",
};

/**
 * The CAPACITY verdict of a team — the answer to "does this team still have
 * room?".
 *
 * The vocabulary is the one of `EstadoCapacidadEquipoChoices`
 * (`backend/modules/salesianos_fest/domain/constants.py`). The backend owns
 * the PRECEDENCE that produces it; the client only renders the code it was
 * told and NEVER compares the players with the cap itself.
 */
const ESTADO_CAPACIDAD_EQUIPO_TONE: Record<string, AdminTone> = {
  CON_CUPOS: "emerald",
  AL_LIMITE: "orange",
};

const ESTADO_CAPACIDAD_EQUIPO_LABEL: Record<string, string> = {
  CON_CUPOS: "Con cupos",
  AL_LIMITE: "Al límite",
};

const ESTADO_ACREDITACION_TONE: Record<string, AdminTone> = {
  PENDIENTE: "amber",
  ACTIVA: "emerald",
  SUSPENDIDA: "orange",
  REVOCADA: "red",
};

const ESTADO_ACREDITACION_LABEL: Record<string, string> = {
  PENDIENTE: "Pendiente",
  ACTIVA: "Activa",
  SUSPENDIDA: "Suspendida",
  REVOCADA: "Revocada",
};

const AUTORIZACION_FIESTA_TONE: Record<string, AdminTone> = {
  AUTOMATICA: "slate",
  AUTORIZADA: "emerald",
  BLOQUEADA: "red",
};

const AUTORIZACION_FIESTA_LABEL: Record<string, string> = {
  AUTOMATICA: "Automática",
  AUTORIZADA: "Autorizada",
  BLOQUEADA: "Bloqueada",
};

const RESULTADO_ACCESO_TONE: Record<string, AdminTone> = {
  PERMITIDO: "emerald",
  DENEGADO: "red",
};

const RESULTADO_ACCESO_LABEL: Record<string, string> = {
  PERMITIDO: "Permitido",
  DENEGADO: "Denegado",
};

const ESTADO_POOL_TONE: Record<string, AdminTone> = {
  LISTO: "emerald",
  ESPERANDO_PAGO: "amber",
  SIN_CAPACIDAD: "orange",
  CUPO_POR_ASIGNAR: "blue",
};

const ESTADO_POOL_LABEL: Record<string, string> = {
  LISTO: "Listo para equipo",
  ESPERANDO_PAGO: "Esperando pago",
  SIN_CAPACIDAD: "Sin capacidad pagada",
  CUPO_POR_ASIGNAR: "Cupo por asignar",
};

const ESTADO_ASIGNACION_TONE: Record<string, AdminTone> = {
  ACTIVA: "emerald",
  LIBERADA: "slate",
  REVOCADA: "red",
};

const ESTADO_ASIGNACION_LABEL: Record<string, string> = {
  ACTIVA: "Activa",
  LIBERADA: "Liberada",
  REVOCADA: "Revocada",
};

const ROL_PARTICIPANTE_LABEL: Record<string, string> = {
  J: "Jugador",
  C: "Capitán",
  D: "Delegado",
};

const ESTADO_PERSONA_LABEL: Record<string, string> = {
  A: "Activo",
  R: "Retirado",
};

const ESTADO_PARTICIPACION_LABEL: Record<string, string> = {
  A: "Activa",
  R: "Retirada",
};

const TIPO_COMPRA_LABEL: Record<string, string> = {
  INICIAL: "Inicial",
  AMPLIACION: "Ampliación",
  PASE: "Pase de fiesta",
};

const TIPO_COMPRA_TONE: Record<string, AdminTone> = {
  INICIAL: "brand",
  AMPLIACION: "violet",
  PASE: "cyan",
};

const TIPO_ACEPTACION_LABEL: Record<string, string> = {
  BASES: "Bases del evento",
  APTITUD_FISICA: "Aptitud física",
  IMAGEN: "Uso de imagen",
};

const MEDIO_ACEPTACION_LABEL: Record<string, string> = {
  WEB: "Formulario web",
  MOBILE: "Aplicación móvil",
  PAPER: "Papel",
};

const ESTADO_TRANSACCION_TONE: Record<string, AdminTone> = {
  PENDIENTE: "amber",
  EXITO: "emerald",
  FALLIDO: "red",
  CANCELADO: "slate",
};

const ESTADO_TRANSACCION_LABEL: Record<string, string> = {
  PENDIENTE: "Pendiente",
  EXITO: "Éxito",
  FALLIDO: "Fallido",
  CANCELADO: "Cancelado",
};

/**
 * The OPERATOR VERDICT of a payment — the ONE answer to "is this payment
 * done?".
 *
 * The vocabulary is the one of `EstadoOperativoPago`
 * (`backend/modules/pagos/domain/constants.py`). The backend owns the
 * PRECEDENCE that produces it; the client only renders the code it was told
 * and NEVER recomputes it.
 */
const ESTADO_OPERATIVO_PAGO_TONE: Record<string, AdminTone> = {
  SIN_ORDEN: "slate",
  PAGADA: "emerald",
  PAGADA_SIN_LIQUIDAR: "orange",
  PAGADA_SIN_EVIDENCIA: "red",
  PAGADA_SIN_FECHA: "amber",
  PENDIENTE: "amber",
  CANCELADA: "rose",
  VENCIDA: "red",
};

const ESTADO_OPERATIVO_PAGO_LABEL: Record<string, string> = {
  SIN_ORDEN: "Sin orden",
  PAGADA: "Pagada",
  PAGADA_SIN_LIQUIDAR: "Pagada sin liquidar",
  PAGADA_SIN_EVIDENCIA: "Pagada sin evidencia",
  PAGADA_SIN_FECHA: "Pagada sin fecha",
  PENDIENTE: "Pendiente",
  CANCELADA: "Cancelada",
  VENCIDA: "Vencida",
};

/**
 * The NOTE of the codes that name a discrepancy between the facts.
 *
 * The marker comes from the VERDICT, never from a comparison the client
 * makes: the backend already decided that the facts do not line up (it
 * answered `PAGADA_SIN_…` instead of `PAGADA`), so the client only renders
 * the sentence of the code it was given. A code without an entry has no
 * marker.
 */
const AVISO_ESTADO_OPERATIVO_PAGO: Record<string, string> = {
  PAGADA_SIN_LIQUIDAR:
    "La orden está pagada pero la compra no está liquidada: los derechos todavía no se activaron.",
  PAGADA_SIN_EVIDENCIA:
    "La orden está pagada pero no hay evidencia correlacionada que la respalde.",
  PAGADA_SIN_FECHA:
    "La orden está pagada y respaldada, pero no registra la fecha del pago.",
};

/**
 * The origin of the payment EVIDENCE — NOT a payment state.
 *
 * `SIN_PAGO` means "there is nothing to verify", so the label says
 * "Sin evidencia" and never "Sin pago": a row without evidence is not
 * necessarily a row without a payment.
 */
const ORIGEN_PAGO_TONE: Record<string, AdminTone> = {
  IZIPAY: "emerald",
  MANUAL: "violet",
  SIN_PAGO: "amber",
};

const ORIGEN_PAGO_LABEL: Record<string, string> = {
  IZIPAY: "Izipay",
  MANUAL: "Manual",
  SIN_PAGO: "Sin evidencia",
};

const ESTADO_APROBACION_MANUAL_TONE: Record<string, AdminTone> = {
  APROBADA: "emerald",
  ANULADA: "rose",
};

const ESTADO_APROBACION_MANUAL_LABEL: Record<string, string> = {
  APROBADA: "Aprobada",
  ANULADA: "Anulada",
};

const CANAL_PAGO_MANUAL_LABEL: Record<string, string> = {
  TRANSFERENCIA_BANCARIA: "Transferencia bancaria",
  EFECTIVO: "Efectivo",
  YAPE: "Yape",
  PLIN: "Plin",
  OTRO: "Otro",
};

function tono(mapa: Record<string, AdminTone>, valor: string): AdminTone {
  return mapa[valor] ?? "slate";
}

function etiqueta(
  mapa: Record<string, string>,
  valor: string | null | undefined,
): string {
  if (!valor) return "—";
  return mapa[valor] ?? valor;
}

/** Tone of a commercial purchase state. */
export function estadoCompraTone(estado: string): AdminTone {
  return tono(ESTADO_COMPRA_TONE, estado);
}

/** Label of a commercial purchase state. */
export function estadoCompraLabel(estado: string): string {
  return etiqueta(ESTADO_COMPRA_LABEL, estado);
}

/** Tone of a payment order state. */
export function estadoOrdenTone(estado: string): AdminTone {
  return tono(ESTADO_ORDEN_TONE, estado);
}

/** Label of a payment order state. */
export function estadoOrdenLabel(estado: string): string {
  return etiqueta(ESTADO_ORDEN_LABEL, estado);
}

/** Tone of a team state. */
export function estadoEquipoTone(estado: string): AdminTone {
  return tono(ESTADO_EQUIPO_TONE, estado);
}

/** Label of a team state. */
export function estadoEquipoLabel(estado: string): string {
  return etiqueta(ESTADO_EQUIPO_LABEL, estado);
}

/** Tone of the derived roster completeness. */
export function rosterTone(estado: string): AdminTone {
  return tono(ROSTER_TONE, estado);
}

/** Label of the derived roster completeness. */
export function rosterLabel(estado: string): string {
  return etiqueta(ROSTER_LABEL, estado);
}

/**
 * Tone of the capacity verdict of a team.
 *
 * An unknown verdict is rendered neutrally: the UI never invents a semantic
 * it was not told.
 */
export function estadoCapacidadEquipoTone(estado: string): AdminTone {
  return tono(ESTADO_CAPACIDAD_EQUIPO_TONE, estado);
}

/** Label of the capacity verdict of a team ("Al límite" when it is full). */
export function estadoCapacidadEquipoLabel(estado: string): string {
  return etiqueta(ESTADO_CAPACIDAD_EQUIPO_LABEL, estado);
}

/** Tone of an accreditation state. */
export function estadoAcreditacionTone(estado: string): AdminTone {
  return tono(ESTADO_ACREDITACION_TONE, estado);
}

/** Label of an accreditation state. */
export function estadoAcreditacionLabel(estado: string): string {
  return etiqueta(ESTADO_ACREDITACION_LABEL, estado);
}

/** Tone of the party authorization override. */
export function autorizacionFiestaTone(estado: string): AdminTone {
  return tono(AUTORIZACION_FIESTA_TONE, estado);
}

/** Label of the party authorization override. */
export function autorizacionFiestaLabel(estado: string): string {
  return etiqueta(AUTORIZACION_FIESTA_LABEL, estado);
}

/** Tone of an access attempt result. */
export function resultadoAccesoTone(resultado: string): AdminTone {
  return tono(RESULTADO_ACCESO_TONE, resultado);
}

/** Label of an access attempt result. */
export function resultadoAccesoLabel(resultado: string): string {
  return etiqueta(RESULTADO_ACCESO_LABEL, resultado);
}

/** Tone of the derived pool eligibility. */
export function estadoPoolTone(estado: string): AdminTone {
  return tono(ESTADO_POOL_TONE, estado);
}

/** Label of the derived pool eligibility. */
export function estadoPoolLabel(estado: string): string {
  return etiqueta(ESTADO_POOL_LABEL, estado);
}

/** Tone of a cup assignment state. */
export function estadoAsignacionTone(estado: string): AdminTone {
  return tono(ESTADO_ASIGNACION_TONE, estado);
}

/** Label of a cup assignment state. */
export function estadoAsignacionLabel(estado: string): string {
  return etiqueta(ESTADO_ASIGNACION_LABEL, estado);
}

/** Label of a roster role. */
export function rolParticipanteLabel(rol: string): string {
  return etiqueta(ROL_PARTICIPANTE_LABEL, rol);
}

/** Label of the state of a registered person. */
export function estadoPersonaLabel(estado: string): string {
  return etiqueta(ESTADO_PERSONA_LABEL, estado);
}

/** Label of the state of a roster row. */
export function estadoParticipacionLabel(estado: string): string {
  return etiqueta(ESTADO_PARTICIPACION_LABEL, estado);
}

/** Label of a purchase type. */
export function tipoCompraLabel(tipo: string): string {
  return etiqueta(TIPO_COMPRA_LABEL, tipo);
}

/** Tone of a purchase type (INICIAL, AMPLIACION or PASE). */
export function tipoCompraTone(tipo: string): AdminTone {
  return tono(TIPO_COMPRA_TONE, tipo);
}

/** Label of a legal acceptance type. */
export function tipoAceptacionLabel(tipo: string): string {
  return etiqueta(TIPO_ACEPTACION_LABEL, tipo);
}

/** Label of the medium of a legal acceptance. */
export function medioAceptacionLabel(medio: string): string {
  return etiqueta(MEDIO_ACEPTACION_LABEL, medio);
}

/** Tone of a payment attempt state. */
export function estadoTransaccionTone(estado: string): AdminTone {
  return tono(ESTADO_TRANSACCION_TONE, estado);
}

/** Label of a payment attempt state. */
export function estadoTransaccionLabel(estado: string): string {
  return etiqueta(ESTADO_TRANSACCION_LABEL, estado);
}

/**
 * Tone of the operator verdict of a payment.
 *
 * An unknown verdict is rendered neutrally: the UI never invents a semantic
 * it was not told.
 */
export function estadoOperativoPagoTone(estado: string): AdminTone {
  return tono(ESTADO_OPERATIVO_PAGO_TONE, estado);
}

/** Label of the operator verdict of a payment. */
export function estadoOperativoPagoLabel(estado: string): string {
  return etiqueta(ESTADO_OPERATIVO_PAGO_LABEL, estado);
}

/**
 * Note of the verdict codes that name a discrepancy between the facts.
 *
 * It is EMPTY for a verdict without a discrepancy: the marker belongs to the
 * codes that name one.
 */
export function estadoOperativoPagoAviso(estado: string): string {
  return AVISO_ESTADO_OPERATIVO_PAGO[estado] ?? "";
}

/** Tone of the origin of the payment evidence (IZIPAY, MANUAL, SIN_PAGO). */
export function origenPagoTone(origen: string): AdminTone {
  return tono(ORIGEN_PAGO_TONE, origen);
}

/** Label of the origin of the payment evidence ("Sin evidencia" when none). */
export function origenPagoLabel(origen: string): string {
  return etiqueta(ORIGEN_PAGO_LABEL, origen);
}

/** Tone of the state of a manual payment approval. */
export function estadoAprobacionManualTone(estado: string): AdminTone {
  return tono(ESTADO_APROBACION_MANUAL_TONE, estado);
}

/** Label of the state of a manual payment approval. */
export function estadoAprobacionManualLabel(estado: string): string {
  return etiqueta(ESTADO_APROBACION_MANUAL_LABEL, estado);
}

/** Label of the channel of a manual payment. */
export function canalPagoManualLabel(canal: string): string {
  return etiqueta(CANAL_PAGO_MANUAL_LABEL, canal);
}
