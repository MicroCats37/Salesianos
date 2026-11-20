/**
 * The vocabulary of the competitions area.
 *
 * Every label of this file is a 1:1 mirror of a backend `TextChoices`: the
 * code AND its wording come from
 * `Aplicacion/backend/modules/competencias/domain/constants.py`
 * (`EstadoCompetencia`, `EstadoCompetenciaEquipo`, `EstadoRonda`,
 * `EstadoEncuentro`, `MotivoNoElegibilidad`, `SlotDestino`). Nothing here is
 * invented and nothing here is a rule: the module publishes the code, the
 * client resolves the wording and never the other way round (`SH-03` §6).
 *
 * The presenters publish the CODE without the wording, so the ADAPTER
 * resolves it and both travel together (`EstadoDeclarado`). A code that is
 * not in the dictionary is NOT guessed: it falls back to the code itself and
 * to the `desconocido` bucket, so an unknown state is visible instead of
 * silently painted as something it is not.
 */

import type {
  EstadoConRol,
  EstadoDeclarado,
  RolEstado,
} from "../types/competencia.types";

/** The wording of a code, or `null` when the code is not in the dictionary. */
type Diccionario = Readonly<Record<string, string>>;

/** `EstadoCompetencia` — the lifecycle of a competition. */
export const ESTADOS_COMPETENCIA: Diccionario = {
  PLANIFICADA: "Planificada",
  EN_CURSO: "En curso",
  FINALIZADA: "Finalizada",
  CANCELADA: "Cancelada",
};

/** `EstadoCompetenciaEquipo` — the participation of a team in the bracket. */
export const ESTADOS_EQUIPO_COMPETENCIA: Diccionario = {
  ACTIVO: "Activo",
  RETIRADO: "Retirado",
};

/** `EstadoRonda` — the state of a round of the bracket. */
export const ESTADOS_RONDA: Diccionario = {
  ACTIVA: "Activa",
  INVALIDADA: "Invalidada",
};

/** `EstadoEncuentro` — the lifecycle of an encounter. */
export const ESTADOS_ENCUENTRO: Diccionario = {
  BORRADOR: "Borrador",
  PROGRAMADO: "Programado",
  EN_CURSO: "En curso",
  FINALIZADO: "Finalizado",
  CANCELADO: "Cancelado",
};

/**
 * `MotivoNoElegibilidad` — why a candidate team cannot compete.
 *
 * The reason is the OWNER of the registration: this module publishes its code
 * and never guesses it (`QA-K01`).
 */
export const MOTIVOS_NO_ELIGIBILIDAD: Diccionario = {
  ELEGIBLE: "Elegible",
  EQUIPO_NO_ENCONTRADO: "El equipo no existe",
  EDICION_DISTINTA: "El equipo pertenece a otra edición",
  DISCIPLINA_DISTINTA: "El equipo pertenece a otra disciplina",
  DISCIPLINA_INACTIVA: "La disciplina no está activa",
  INSCRIPCION_CANCELADA: "La inscripción está cancelada",
  EQUIPO_NO_ACTIVO: "El equipo está retirado",
  SIN_PLANTILLA: "El equipo no tiene participantes activos",
  PLANTILLA_INCOMPLETA: "El equipo no alcanza el mínimo de participantes",
};

/**
 * The actions the backend admits in each state of an encounter.
 *
 * Mirrors `proyeccion.ACCIONES_POR_ESTADO`. The list is INFORMATIVE: the
 * authorisation is the backend's (`RN-A01`). The interface uses it to hide
 * the impossible, never to authorise.
 */
export const ACCIONES_ENCUENTRO: Diccionario = {
  asignar_participantes: "Asignar participantes",
  programar: "Programar",
  enlazar: "Enlazar con el cuadro",
  marcar_bye: "Marcar como pase libre",
  iniciar: "Iniciar el encuentro",
  desprogramar: "Quitar la programación",
  registrar_resultado: "Registrar el resultado",
  cancelar: "Cancelar el encuentro",
  corregir: "Corregir el resultado",
  avanzar: "Confirmar el avance",
};

/**
 * The buckets that paint each code.
 *
 * The bucket is PRESENTATIONAL. It says how the chip looks, never what the
 * state means (`SH-01` §3.2).
 */
const BOLES: Readonly<Record<string, RolEstado>> = {
  PLANIFICADA: "planificado",
  PROGRAMADO: "planificado",
  ACTIVA: "activo",
  ACTIVO: "activo",
  ELEGIBLE: "elegible",
  EN_CURSO: "en-curso",
  FINALIZADO: "finalizado",
  BORRADOR: "borrador",
  CANCELADA: "cancelado",
  CANCELADO: "cancelado",
  INVALIDADA: "cancelado",
  RETIRADO: "retirado",
};

/**
 * Resolve a code into the state that travels with its label.
 *
 * A code outside the dictionary keeps ITS OWN text: an unknown state is
 * shown, never hidden and never guessed.
 */
export function resolverEstado(
  codigo: string,
  diccionario: Diccionario,
): EstadoDeclarado {
  const etiqueta = diccionario[codigo];
  return {
    codigo,
    etiqueta: etiqueta ?? codigo,
  };
}

/** Resolve the state of a competition. */
export function estadoCompetencia(codigo: string): EstadoConRol {
  return {
    estado: resolverEstado(codigo, ESTADOS_COMPETENCIA),
    rol: BOLES[codigo] ?? "bloqueado",
  };
}

/** Resolve the state of the participation of a team. */
export function estadoEquipoCompetencia(codigo: string): EstadoConRol {
  return {
    estado: resolverEstado(codigo, ESTADOS_EQUIPO_COMPETENCIA),
    rol: BOLES[codigo] ?? "bloqueado",
  };
}

/** Resolve the state of a round. */
export function estadoRonda(codigo: string): EstadoConRol {
  return {
    estado: resolverEstado(codigo, ESTADOS_RONDA),
    rol: BOLES[codigo] ?? "bloqueado",
  };
}

/** Resolve the state of an encounter. */
export function estadoEncuentro(codigo: string): EstadoConRol {
  return {
    estado: resolverEstado(codigo, ESTADOS_ENCUENTRO),
    rol: BOLES[codigo] ?? "bloqueado",
  };
}

/**
 * Resolve the eligibility verdict of a candidate team.
 *
 * An eligible team is `elegible`; an ineligible one is `bloqueado` and its
 * reason travels with it. The reason is NEVER inferred from the counts.
 */
export function veredictoElegibilidad(
  codigo: string,
  esElegible: boolean,
): EstadoConRol {
  return {
    estado: resolverEstado(codigo, MOTIVOS_NO_ELIGIBILIDAD),
    rol: esElegible ? "elegible" : "bloqueado",
  };
}

/** The wording of one of the actions the backend advertises. */
export function etiquetaAccion(codigo: string): string {
  return ACCIONES_ENCUENTRO[codigo] ?? codigo;
}
