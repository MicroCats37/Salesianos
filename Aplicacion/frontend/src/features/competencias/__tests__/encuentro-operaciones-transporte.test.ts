import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiSend } = vi.hoisted(() => ({ apiSend: vi.fn() }));

vi.mock("@/lib/api", () => ({
  apiSend,
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
}));

import { aPayloadProgramacion } from "../components/DialogoProgramacionEncuentro";
import { aPayloadResultado } from "../components/DialogoResultadoEncuentro";
import {
  actualizarEncuentro,
  confirmarAvance,
  corregirEncuentro,
  previsualizarAvance,
  previsualizarCorreccion,
  registrarResultado,
  rutasCompetencias,
} from "../services/competencia.service";

/**
 * The transport of the LIFECYCLE of an encounter (`ADM-11`).
 *
 * The double lives at the TRANSPORT boundary (`apiSend`), so the URL, the
 * method, the payload and the envelope are all under test.
 *
 * The suite freezes FOUR contracts:
 *
 * 1. the ROUTE and the METHOD of every command (they are REGISTERED routes:
 *    `CompetenciasController`);
 * 2. the PAYLOAD: it carries `expected_version` and ONLY the declared fields;
 * 3. the ENVELOPE: an answer that does not comply is a LOUD failure;
 * 4. the WINNER: it is DECLARED, never derived from the score.
 */
const COMPETENCIA = "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70";
const ENCUENTRO = "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80";
const PARTICIPACION_1 = "44444444-4444-4444-8444-444444444444";
const PARTICIPACION_2 = "66666666-6666-4666-8666-666666666666";

/** An encounter, exactly as the presenter publishes it. */
const ENCUENTRO_PUBLISH = {
  id: ENCUENTRO,
  ronda_id: "22222222-2222-4222-8222-222222222222",
  ronda_etiqueta: "Cuartos de final",
  ronda_orden: 1,
  competencia_id: COMPETENCIA,
  orden: 1,
  estado: "EN_CURSO",
  es_bye: false,
  participantes: [
    {
      slot: "PARTICIPANTE_1",
      competencia_equipo_id: PARTICIPACION_1,
      equipo_id: "55555555-5555-4555-8555-555555555555",
      equipo_nombre: "Salesianos A",
      orden: 1,
    },
    {
      slot: "PARTICIPANTE_2",
      competencia_equipo_id: PARTICIPACION_2,
      equipo_id: "77777777-7777-4777-8777-777777777777",
      equipo_nombre: "Salesianos B",
      orden: 2,
    },
  ],
  inicio_programado: "2027-03-14T15:00:00Z",
  fin_programado: "2027-03-14T16:00:00Z",
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: "",
  ganador_equipo_id: null,
  ganador_equipo_nombre: null,
  siguiente_encuentro_id: null,
  slot_destino: null,
  iniciado_en: "2027-03-14T15:03:00Z",
  finalizado_en: null,
  version: 4,
  acciones: ["registrar_resultado", "cancelar"],
};

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

beforeEach(() => {
  apiSend.mockReset();
});

describe("el cliente del ciclo de vida del encuentro", () => {
  it("la edición del encuentro viaja en la ruta y NUNCA en el cuerpo", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope(ENCUENTRO_PUBLISH),
    });

    await actualizarEncuentro(COMPETENCIA, ENCUENTRO, {
      estado: "EN_CURSO",
      motivo: "Inicio del encuentro",
      expected_version: 4,
    });

    expect(apiSend).toHaveBeenCalledWith(
      "patch",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}`,
      {
        estado: "EN_CURSO",
        motivo: "Inicio del encuentro",
        expected_version: 4,
      },
    );
  });

  it("el resultado se registra en su ruta y con el ganador declarado", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({
        encuentro: ENCUENTRO_PUBLISH,
        ganador_equipo_id: "77777777-7777-4777-8777-777777777777",
        ganador_equipo_nombre: "Salesianos B",
      }),
    });

    await registrarResultado(COMPETENCIA, ENCUENTRO, {
      ganador_id: PARTICIPACION_2,
      puntaje_1: 9,
      puntaje_2: 4,
      marcador_detalle: "Set 1: 9-4",
      motivo: "Registro del resultado",
      expected_version: 4,
    });

    expect(apiSend).toHaveBeenCalledWith(
      "post",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/resultado`,
      {
        ganador_id: PARTICIPACION_2,
        puntaje_1: 9,
        puntaje_2: 4,
        marcador_detalle: "Set 1: 9-4",
        motivo: "Registro del resultado",
        expected_version: 4,
      },
    );
  });

  it("la vista previa del avance NO escribe y no lleva cuerpo", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({
        encuentro_id: ENCUENTRO,
        siguiente_encuentro_id: "99999999-9999-4999-8999-999999999999",
        ganador_equipo_id: "55555555-5555-4555-8555-555555555555",
        ganador_equipo_nombre: "Salesianos A",
        slot_destino: "PARTICIPANTE_1",
        ocupante_actual_equipo_id: null,
        bloqueado: false,
        motivo_bloqueo: null,
        ya_propagado: false,
        puede_confirmar: true,
      }),
    });

    const vistaPrevia = await previsualizarAvance(COMPETENCIA, ENCUENTRO);

    expect(vistaPrevia.puede_confirmar).toBe(true);
    expect(apiSend).toHaveBeenCalledWith(
      "post",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/avance/preview`,
      undefined,
    );
  });

  it("la confirmación del avance lleva la versión que el operador conhece", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({
        encuentro_origen_id: ENCUENTRO,
        siguiente_encuentro_id: "99999999-9999-4999-8999-999999999999",
        slot_destino: "PARTICIPANTE_1",
        ganador_equipo_id: "55555555-5555-4555-8555-555555555555",
        ganador_equipo_nombre: "Salesianos A",
        ya_aplicado: false,
        destino: ENCUENTRO_PUBLISH,
      }),
    });

    await confirmarAvance(COMPETENCIA, ENCUENTRO, {
      motivo: "Avance confirmado",
      expected_version: 7,
    });

    expect(apiSend).toHaveBeenCalledWith(
      "post",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/avance`,
      { motivo: "Avance confirmado", expected_version: 7 },
    );
  });

  it("la vista previa de la corrección lleva el ganador nuevo", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({
        encuentro_id: ENCUENTRO,
        ganador_actual_equipo_id: null,
        ganador_nuevo_equipo_id: "77777777-7777-4777-8777-777777777777",
        ganador_nuevo_equipo_nombre: "Salesianos B",
        requiere_override: false,
        total_afectados: 0,
        descendientes: [],
        puede_confirmar: true,
      }),
    });

    await previsualizarCorreccion(COMPETENCIA, ENCUENTRO, PARTICIPACION_2);

    expect(apiSend).toHaveBeenCalledWith(
      "post",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/correccion/preview`,
      { ganador_id: PARTICIPACION_2 },
    );
  });

  it("la corrección lleva el motivo, la autorización y el impacto aceptado", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({
        encuentro_id: ENCUENTRO,
        ganador_nuevo_equipo_id: "77777777-7777-4777-8777-777777777777",
        ganador_nuevo_equipo_nombre: "Salesianos B",
        descendientes_afectados: 0,
        override_aplicado: false,
        encuentro: ENCUENTRO_PUBLISH,
        descendientes: [],
      }),
    });

    await corregirEncuentro(COMPETENCIA, ENCUENTRO, {
      ganador_id: PARTICIPACION_2,
      motivo: "El resultado se registró con el equipo equivocado",
      override: false,
      acepta_impacto: true,
      expected_version: 7,
    });

    expect(apiSend).toHaveBeenCalledWith(
      "post",
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/correccion`,
      {
        ganador_id: PARTICIPACION_2,
        motivo: "El resultado se registró con el equipo equivocado",
        override: false,
        acepta_impacto: true,
        expected_version: 7,
      },
    );
  });

  it("un cuerpo que no cumple el contrato es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue({ status: 200, data: envelope({ version: 4 }) });

    await expect(
      actualizarEncuentro(COMPETENCIA, ENCUENTRO, {
        estado: "EN_CURSO",
        motivo: "Inicio del encuentro",
        expected_version: 4,
      }),
    ).rejects.toThrow();
  });

  it("el 204 NUNCA se parsea", async () => {
    apiSend.mockResolvedValue({ status: 204, data: null });

    await expect(
      actualizarEncuentro(COMPETENCIA, ENCUENTRO, {
        estado: "EN_CURSO",
        motivo: "Inicio del encuentro",
        expected_version: 4,
      }),
    ).rejects.toThrow(/sin contenido/i);
  });

  it("las rutas del lifecycle son las del controller registrado", () => {
    expect(rutasCompetencias.encuentro(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}`,
    );
    expect(rutasCompetencias.resultado(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/resultado`,
    );
    expect(rutasCompetencias.avancePreview(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/avance/preview`,
    );
    expect(rutasCompetencias.avance(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/avance`,
    );
    expect(rutasCompetencias.correccionPreview(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/correccion/preview`,
    );
    expect(rutasCompetencias.correccion(COMPETENCIA, ENCUENTRO)).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}/correccion`,
    );
  });
});

describe("el mapeo del formulario al comando", () => {
  it("el ganador viaja como lo que el operador ELIGIÓ, no como el que va ganando", () => {
    const payload = aPayloadResultado(
      {
        ganador_id: PARTICIPACION_2,
        puntaje_1: "9",
        puntaje_2: "4",
        marcador_detalle: "Set 1: 9-4",
        motivo: "Registro del resultado",
      },
      4,
    );

    // El marcador dice 9-4 y el ganador es el SEGUNDO: el comando lo dice
    // así y el backend lo valida (`GOV-02-RB-05c`).
    expect(payload.ganador_id).toBe(PARTICIPACION_2);
    expect(payload.puntaje_1).toBe(9);
    expect(payload.puntaje_2).toBe(4);
    expect(payload.expected_version).toBe(4);
  });

  it("un puntaje ausente viaja como ausencia, no como cero", () => {
    const payload = aPayloadResultado(
      {
        ganador_id: PARTICIPACION_1,
        puntaje_1: "",
        puntaje_2: "",
        marcador_detalle: "",
        motivo: "Registro del resultado",
      },
      1,
    );

    expect(payload.puntaje_1).toBeNull();
    expect(payload.puntaje_2).toBeNull();
    expect(payload.marcador_detalle).toBeNull();
  });

  it("la hora local del operador viaja con el desplazamiento de la edición", () => {
    const payload = aPayloadProgramacion(
      {
        inicio_programado: "2027-03-14T10:00",
        fin_programado: "2027-03-14T11:00",
        motivo: "Programación del encuentro",
      },
      4,
    );

    expect(payload.inicio_programado).toBe("2027-03-14T10:00:00-05:00");
    expect(payload.fin_programado).toBe("2027-03-14T11:00:00-05:00");
    expect(payload.expected_version).toBe(4);
  });
});
