import type { AdminTone } from "@/features/admin/utils";
import type { Encuentro, RondaCuadro } from "../schemas";
import {
  estadoEncuentroLabel,
  estadoEncuentroTone,
  estadoRondaLabel,
  estadoRondaTone,
} from "./competencias.estado.utils";
import {
  competenciasHora,
  competenciasMinutosDelDia,
} from "./competencias.url.utils";

/**
 * Mapping of the bracket and of the agenda — the DERIVED views of the
 * payloads of the backend.
 *
 * The mapping NEVER invents a participant, an advance or a schedule: an empty
 * or partial bracket must stay legible and editable without autocompleting
 * anything (`sdd/enfrentamientos-competencias/spec`, requirement
 * "Rondas, byes y cuadros incompletos").
 *
 * The module is dependency-free at runtime (the only import of the barrel of
 * the administration area is a TYPE), so the mapping can be verified
 * deterministically.
 */

/** Label of a slot that is still empty. */
export const COMPETENCIA_SLOT_VACIO = "—";

/** A cell of the bracket: ONE encounter with its two slots. */
export interface CompetenciaCuadroCelda {
  /** The encounter of the cell. */
  encuentro: Encuentro;
  /** Label of the first slot. */
  participante1: string;
  /** Label of the second slot. */
  participante2: string;
  /** Whether the encounter is a bye (exactly one participant). */
  esBye: boolean;
  /** Whether the winner is already known. */
  tieneGanador: boolean;
  /** Whether the encounter has a schedule. */
  tieneHorario: boolean;
  /** Text of the score ("—" when there is none). */
  marcador: string;
  /** Label of the state of the encounter. */
  estado: string;
  /** Tone of the state of the encounter. */
  tono: AdminTone;
}

/** A column of the bracket: a round and its encounters. */
export interface CompetenciaCuadroColumna {
  /** Identifier of the round. */
  id: string;
  /** Label of the round. */
  etiqueta: string;
  /** Order of the round. */
  orden: number;
  /** Label of the state of the round. */
  estado: string;
  /** Tone of the state of the round. */
  tono: AdminTone;
  /** The encounters of the round, in the order of the backend. */
  celdas: CompetenciaCuadroCelda[];
}

/**
 * The text of the score of an encounter.
 *
 * The scores are OPTIONAL and purely informative: they never determine nor
 * contradict the authoritative winner, so an encounter without them shows a
 * dash and never a zero.
 */
export function competenciaMarcador(encuentro: Encuentro): string {
  const puntaje =
    encuentro.puntaje_1 !== null && encuentro.puntaje_2 !== null
      ? `${encuentro.puntaje_1} - ${encuentro.puntaje_2}`
      : "";
  const detalle = (encuentro.marcador_detalle ?? "").trim();

  if (puntaje && detalle) return `${puntaje} · ${detalle}`;
  return puntaje || detalle || COMPETENCIA_SLOT_VACIO;
}

/** Map ONE encounter into a cell of the bracket. */
export function competenciaCelda(encuentro: Encuentro): CompetenciaCuadroCelda {
  return {
    encuentro,
    participante1:
      encuentro.participante_1_nombre?.trim() || COMPETENCIA_SLOT_VACIO,
    participante2:
      encuentro.participante_2_nombre?.trim() || COMPETENCIA_SLOT_VACIO,
    esBye: encuentro.es_bye,
    tieneGanador: Boolean(encuentro.ganador_id),
    tieneHorario: Boolean(
      encuentro.inicio_programado && encuentro.fin_programado,
    ),
    marcador: competenciaMarcador(encuentro),
    estado: estadoEncuentroLabel(encuentro.estado),
    tono: estadoEncuentroTone(encuentro.estado),
  };
}

/**
 * Map the rounds of a bracket into its COLUMNS.
 *
 * The rounds are ordered by their manual order and the encounters of a round
 * keep the order of the backend. An empty bracket maps to an empty list of
 * columns: it is a valid state, never an error.
 */
export function competenciaCuadroColumnas(
  rondas: RondaCuadro[],
): CompetenciaCuadroColumna[] {
  return [...rondas]
    .sort((a, b) => a.orden - b.orden)
    .map((ronda) => ({
      id: ronda.id,
      etiqueta: ronda.etiqueta,
      orden: ronda.orden,
      estado: estadoRondaLabel(ronda.estado),
      tono: estadoRondaTone(ronda.estado),
      celdas: ronda.encuentros.map((encuentro) => competenciaCelda(encuentro)),
    }));
}

/** A row of the temporal agenda. */
export interface AgendaEncuentroFila {
  /** The encounter of the row. */
  encuentro: Encuentro;
  /** Start of the schedule (`HH:mm`), empty when it has none. */
  inicio: string;
  /** End of the schedule (`HH:mm`), empty when it has none. */
  fin: string;
  /** Duration in minutes, or `null` when it cannot be derived. */
  duracionMinutos: number | null;
  /** Text of the schedule range. */
  horario: string;
  /** Labels of the participants that are already known. */
  participantes: string[];
  /** Label of the competition the encounter belongs to. */
  competencia: string;
  /** Label of the state of the encounter. */
  estado: string;
  /** Tone of the state of the encounter. */
  tono: AdminTone;
  /** Whether the encounter is a bye. */
  esBye: boolean;
  /** Text of the score. */
  marcador: string;
}

/** A temporal slot of the agenda. */
export interface AgendaFranja {
  /** Stable key of the slot. */
  clave: string;
  /** Label of the slot (`HH:mm`, or "Sin horario"). */
  etiqueta: string;
  /** Encounters of the slot. */
  encuentros: AgendaEncuentroFila[];
}

/** Key of the slot that groups the encounters without a schedule. */
export const AGENDA_CLAVE_SIN_HORARIO = "sin-horario";

/** Map ONE encounter into a row of the agenda. */
export function agendaFila(encuentro: Encuentro): AgendaEncuentroFila {
  const inicio = competenciasHora(encuentro.inicio_programado);
  const fin = competenciasHora(encuentro.fin_programado);

  const inicioMinutos = competenciasMinutosDelDia(encuentro.inicio_programado);
  const finMinutos = competenciasMinutosDelDia(encuentro.fin_programado);
  const duracionMinutos =
    inicioMinutos !== null && finMinutos !== null && finMinutos > inicioMinutos
      ? finMinutos - inicioMinutos
      : null;

  const participantes = [
    encuentro.participante_1_nombre?.trim(),
    encuentro.participante_2_nombre?.trim(),
  ].filter((nombre): nombre is string => Boolean(nombre));

  return {
    encuentro,
    inicio,
    fin,
    duracionMinutos,
    horario: inicio && fin ? `${inicio} – ${fin}` : "Sin horario",
    participantes,
    competencia: encuentro.competencia_nombre?.trim() || "—",
    estado: estadoEncuentroLabel(encuentro.estado),
    tono: estadoEncuentroTone(encuentro.estado),
    esBye: encuentro.es_bye,
    marcador: competenciaMarcador(encuentro),
  };
}

/**
 * Map the encounters of ONE day into its TEMPORAL slots.
 *
 * The encounters are grouped by the instant they start and the slots are
 * ordered chronologically; the encounters without a schedule are the LAST
 * slot, because they have no place in the day.
 */
export function competenciaAgendaFranjas(
  encuentros: Encuentro[],
): AgendaFranja[] {
  const grupos = new Map<string, AgendaEncuentroFila[]>();

  for (const encuentro of encuentros) {
    const clave = encuentro.inicio_programado ?? "";
    const fila = agendaFila(encuentro);
    const actual = grupos.get(clave);

    if (actual) {
      actual.push(fila);
    } else {
      grupos.set(clave, [fila]);
    }
  }

  const franjas: AgendaFranja[] = [];

  for (const [clave, filas] of grupos) {
    filas.sort((a, b) => {
      if (a.inicio !== b.inicio) return a.inicio.localeCompare(b.inicio);
      return a.encuentro.orden - b.encuentro.orden;
    });

    franjas.push({
      clave: clave || AGENDA_CLAVE_SIN_HORARIO,
      etiqueta: clave ? (filas[0]?.inicio ?? clave) : "Sin horario",
      encuentros: filas,
    });
  }

  return franjas.sort((a, b) => {
    if (a.clave === AGENDA_CLAVE_SIN_HORARIO) return 1;
    if (b.clave === AGENDA_CLAVE_SIN_HORARIO) return -1;
    return a.etiqueta.localeCompare(b.etiqueta);
  });
}
