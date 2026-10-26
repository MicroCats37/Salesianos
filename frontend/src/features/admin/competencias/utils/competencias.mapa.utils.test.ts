import { describe, expect, it } from "vitest";
import type { Encuentro, RondaCuadro } from "../schemas";
import {
  AGENDA_CLAVE_SIN_HORARIO,
  competenciaAgendaFranjas,
  competenciaCuadroColumnas,
  competenciaMarcador,
} from "./competencias.mapa.utils";

/**
 * Focused test of the DERIVED views of the bracket and of the agenda.
 *
 * The mapping NEVER invents a participant, an advance or a schedule: an empty
 * or partial bracket must stay legible (`sdd/enfrentamientos-competencias/spec`,
 * requirement "Rondas, byes y cuadros incompletos").
 */

function encuentroPayload(overrides: Partial<Encuentro> = {}): Encuentro {
  return {
    id: "e1",
    ronda_id: "r1",
    ronda_etiqueta: "Cuartos de final",
    ronda_orden: 1,
    competencia_id: "c1",
    competencia_nombre: "Eliminatoria F7 B",
    orden: 1,
    participante_1_id: "eq1",
    participante_1_nombre: "Los Andes",
    participante_2_id: "eq2",
    participante_2_nombre: "San Francisco",
    inicio_programado: "2026-11-16T14:30:00",
    fin_programado: "2026-11-16T15:10:00",
    estado: "PROGRAMADO",
    estado_pre_suspension: null,
    iniciado_en: null,
    finalizado_en: null,
    es_bye: false,
    ganador_id: null,
    puntaje_1: null,
    puntaje_2: null,
    marcador_detalle: "",
    siguiente_encuentro_id: null,
    slot_destino: null,
    ganador_propagado_id: null,
    version: 1,
    ...overrides,
  };
}

function rondaPayload(
  encuentros: Encuentro[],
  overrides: Partial<RondaCuadro> = {},
): RondaCuadro {
  return {
    id: "r1",
    etiqueta: "Cuartos de final",
    orden: 1,
    estado: "ACTIVA",
    encuentros,
    ...overrides,
  };
}

// ── El cuadro ────────────────────────────────────────────────────────────────

describe("el cuadro se mapea en columnas", () => {
  it("ordena las rondas por su orden manual", () => {
    const columnas = competenciaCuadroColumnas([
      rondaPayload([], { id: "r2", etiqueta: "Final", orden: 2 }),
      rondaPayload([], { id: "r1", etiqueta: "Cuartos", orden: 1 }),
    ]);

    expect(columnas.map((columna) => columna.etiqueta)).toEqual([
      "Cuartos",
      "Final",
    ]);
  });

  it("mapea las dos ranuras de un encuentro", () => {
    const columnas = competenciaCuadroColumnas([
      rondaPayload([encuentroPayload()]),
    ]);

    const celda = columnas[0]?.celdas[0];

    expect(celda?.participante1).toBe("Los Andes");
    expect(celda?.participante2).toBe("San Francisco");
    expect(celda?.esBye).toBe(false);
    expect(celda?.tieneGanador).toBe(false);
    expect(celda?.tieneHorario).toBe(true);
    expect(celda?.estado).toBe("Programado");
  });

  it("deja el hueco de una ranura vacia sin inventar un equipo", () => {
    const columnas = competenciaCuadroColumnas([
      rondaPayload([
        encuentroPayload({
          participante_2_id: null,
          participante_2_nombre: null,
        }),
      ]),
    ]);

    expect(columnas[0]?.celdas[0]?.participante2).toBe("—");
  });

  it("reconoce el bye de un encuentro con un solo participante", () => {
    const columnas = competenciaCuadroColumnas([
      rondaPayload([
        encuentroPayload({
          participante_2_id: null,
          participante_2_nombre: null,
          es_bye: true,
          ganador_id: "eq1",
          inicio_programado: null,
          fin_programado: null,
          estado: "FINALIZADO",
        }),
      ]),
    ]);

    const celda = columnas[0]?.celdas[0];

    expect(celda?.esBye).toBe(true);
    expect(celda?.tieneGanador).toBe(true);
    expect(celda?.tieneHorario).toBe(false);
    expect(celda?.estado).toBe("Finalizado");
  });

  it("mapea un cuadro vacio sin inventar rondas", () => {
    expect(competenciaCuadroColumnas([])).toEqual([]);
  });
});

// ── El marcador ──────────────────────────────────────────────────────────────

describe("el marcador es informativo y nunca inventa un resultado", () => {
  it("muestra el puntaje cuando existe", () => {
    expect(
      competenciaMarcador(encuentroPayload({ puntaje_1: 3, puntaje_2: 1 })),
    ).toBe("3 - 1");
  });

  it("muestra el detalle cuando no hay puntaje", () => {
    expect(
      competenciaMarcador(encuentroPayload({ marcador_detalle: "3-0 sets 1" })),
    ).toBe("3-0 sets 1");
  });

  it("muestra un guion cuando no hay nada", () => {
    expect(competenciaMarcador(encuentroPayload())).toBe("—");
  });
});

// ── La agenda ────────────────────────────────────────────────────────────────

describe("la agenda se agrupa en franjas temporales", () => {
  it("ordena las franjas por la hora de inicio", () => {
    const franjas = competenciaAgendaFranjas([
      encuentroPayload({
        id: "e2",
        inicio_programado: "2026-11-16T16:00:00",
        fin_programado: "2026-11-16T16:40:00",
      }),
      encuentroPayload({
        id: "e1",
        inicio_programado: "2026-11-16T14:30:00",
        fin_programado: "2026-11-16T15:10:00",
      }),
    ]);

    expect(franjas.map((franja) => franja.etiqueta)).toEqual([
      "14:30",
      "16:00",
    ]);
  });

  it("agrupa en la misma franja los encuentros que empiezan a la vez", () => {
    const franjas = competenciaAgendaFranjas([
      encuentroPayload({ id: "e1", orden: 1 }),
      encuentroPayload({
        id: "e2",
        orden: 2,
        participante_1_id: "eq3",
        participante_1_nombre: "San Bartolome",
        participante_2_id: "eq4",
        participante_2_nombre: "Independiente",
      }),
    ]);

    expect(franjas).toHaveLength(1);
    expect(franjas[0]?.encuentros).toHaveLength(2);
  });

  it("deja los encuentros sin horario en la ultima franja", () => {
    const franjas = competenciaAgendaFranjas([
      encuentroPayload({
        id: "e1",
        inicio_programado: null,
        fin_programado: null,
      }),
      encuentroPayload({
        id: "e2",
        inicio_programado: "2026-11-16T14:30:00",
        fin_programado: "2026-11-16T15:10:00",
      }),
    ]);

    expect(franjas).toHaveLength(2);
    expect(franjas[0]?.clave).not.toBe(AGENDA_CLAVE_SIN_HORARIO);
    expect(franjas[1]?.clave).toBe(AGENDA_CLAVE_SIN_HORARIO);
    expect(franjas[1]?.etiqueta).toBe("Sin horario");
  });

  it("calcula la duracion del encuentro en minutos", () => {
    const franjas = competenciaAgendaFranjas([encuentroPayload()]);

    expect(franjas[0]?.encuentros[0]?.duracionMinutos).toBe(40);
    expect(franjas[0]?.encuentros[0]?.horario).toBe("14:30 – 15:10");
  });

  it("muestra los participantes que ya existen", () => {
    const franjas = competenciaAgendaFranjas([
      encuentroPayload({
        participante_2_id: null,
        participante_2_nombre: null,
      }),
    ]);

    expect(franjas[0]?.encuentros[0]?.participantes).toEqual(["Los Andes"]);
  });

  it("mapea una agenda vacia sin inventar franjas", () => {
    expect(competenciaAgendaFranjas([])).toEqual([]);
  });
});
