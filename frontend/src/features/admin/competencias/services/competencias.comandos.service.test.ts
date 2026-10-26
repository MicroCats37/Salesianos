// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The transport of the commands of the module.
 *
 * The suite verifies the contract at the HTTP boundary: the exact URL of
 * every command and the EXACT body that travels, validated against the 1:1
 * Zod mirror BEFORE the request leaves.
 */

const { request } = vi.hoisted(() => ({ request: vi.fn() }));

vi.mock("@/lib/api", () => ({
  api: { request },
  default: { request },
}));

import {
  configurarByeEncuentro,
  confirmarCorreccion,
  crearEquipoCompetencia,
  previsualizarAvance,
  programarEncuentro,
} from "../services/competencias.comandos.service";

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const EQUIPO_ID = "33333333-3333-4333-8333-333333333333";
const GANADOR_ID = "44444444-4444-4444-8444-444444444444";

const ENCUENTRO = {
  id: ENCUENTRO_ID,
  ronda_id: "55555555-5555-4555-8555-555555555555",
  ronda_etiqueta: "Final",
  ronda_orden: 4,
  competencia_id: COMPETENCIA_ID,
  competencia_nombre: "Fútbol",
  orden: 1,
  participante_1_id: GANADOR_ID,
  participante_1_nombre: "Los Halcones",
  participante_2_id: null,
  participante_2_nombre: null,
  inicio_programado: null,
  fin_programado: null,
  estado: "BORRADOR",
  estado_pre_suspension: null,
  iniciado_en: null,
  finalizado_en: null,
  es_bye: false,
  ganador_id: null,
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: null,
  siguiente_encuentro_id: null,
  slot_destino: null,
  ganador_propagado_id: null,
  version: 1,
};

function envolver(data: unknown) {
  return { success: true, data, error: null, message: null };
}

const EQUIPO = {
  id: "77777777-7777-4777-8777-777777777777",
  competencia_id: COMPETENCIA_ID,
  equipo_id: EQUIPO_ID,
  equipo_nombre: "Los Halcones",
  orden: 3,
  estado: "ACTIVO",
  version: 1,
};

describe("El transporte de los comandos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    request.mockResolvedValue({ data: envolver(ENCUENTRO) });
  });

  it("registra el equipo en la URL de la competencia", async () => {
    request.mockResolvedValue({ data: envolver(EQUIPO) });

    await crearEquipoCompetencia(COMPETENCIA_ID, {
      equipo_id: EQUIPO_ID,
      orden: 3,
    });

    expect(request).toHaveBeenCalledWith({
      method: "post",
      url: `/administracion/competencias/${COMPETENCIA_ID}/equipos`,
      data: { equipo_id: EQUIPO_ID, orden: 3 },
    });
  });

  it("programa el encuentro con los dos instantes", async () => {
    await programarEncuentro(ENCUENTRO_ID, {
      inicio_programado: "2026-10-25T10:00:00",
      fin_programado: "2026-10-25T10:45:00",
      motivo: "Programacion del encuentro",
      expected_version: 1,
    });

    expect(request).toHaveBeenCalledWith({
      method: "patch",
      url: `/administracion/competencias/encuentros/${ENCUENTRO_ID}/programacion`,
      data: {
        inicio_programado: "2026-10-25T10:00:00",
        fin_programado: "2026-10-25T10:45:00",
        motivo: "Programacion del encuentro",
        expected_version: 1,
      },
    });
  });

  it("configura el bye manual SIN participantes", async () => {
    await configurarByeEncuentro(ENCUENTRO_ID, {
      motivo: "Bye manual por decision del arbitro",
      expected_version: 1,
    });

    expect(request).toHaveBeenCalledWith({
      method: "post",
      url: `/administracion/competencias/encuentros/${ENCUENTRO_ID}/bye`,
      data: {
        motivo: "Bye manual por decision del arbitro",
        expected_version: 1,
      },
    });
  });

  it("previsualiza el avance SIN cuerpo", async () => {
    request.mockResolvedValue({
      data: envolver({
        encuentro_id: ENCUENTRO_ID,
        siguiente_encuentro_id: "66666666-6666-4666-8666-666666666666",
        slot_destino: "PARTICIPANTE_1",
        ganador_id: GANADOR_ID,
        ocupante_actual_id: null,
        ya_propagado: false,
        bloqueado: false,
        motivo_bloqueo: null,
      }),
    });

    await previsualizarAvance(ENCUENTRO_ID);

    expect(request).toHaveBeenCalledWith({
      method: "post",
      url: `/administracion/competencias/encuentros/${ENCUENTRO_ID}/avance/preview`,
      data: undefined,
    });
  });

  it("confirma la correccion con el override y la aceptacion", async () => {
    request.mockResolvedValue({
      data: envolver({
        encuentro_id: ENCUENTRO_ID,
        ganador_id: GANADOR_ID,
        requirio_override: true,
        descendientes_afectados: 1,
        encuentro: ENCUENTRO,
        descendientes: [],
      }),
    });

    await confirmarCorreccion(ENCUENTRO_ID, {
      ganador_id: GANADOR_ID,
      motivo: "Correccion administrativa del ganador",
      override: true,
      acepta_impacto: true,
      expected_version: 1,
    });

    expect(request).toHaveBeenCalledWith({
      method: "post",
      url: `/administracion/competencias/encuentros/${ENCUENTRO_ID}/correccion/confirm`,
      data: {
        ganador_id: GANADOR_ID,
        motivo: "Correccion administrativa del ganador",
        override: true,
        acepta_impacto: true,
        expected_version: 1,
      },
    });
  });

  it("RECHAZA un cuerpo que no cumple el contrato antes de enviarlo", async () => {
    await expect(
      crearEquipoCompetencia(COMPETENCIA_ID, {
        equipo_id: "no-es-un-uuid",
        orden: 3,
      }),
    ).rejects.toThrow();

    expect(request).not.toHaveBeenCalled();
  });
});
