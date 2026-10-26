// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  construirPayloadCorreccion,
  construirPayloadProgramacion,
  construirPayloadResultado,
  invalidarLecturasCompetencia,
  useRegistrarResultadoEncuentro,
} from "./useCompetenciasComandos";

/**
 * The mutations of the module.
 *
 * The suite verifies the two contracts that the editors and the dialogs
 * depend on:
 *
 * 1. the EXACT payload that travels to the API (the manual order, the
 *    audited motive and the optimistic lock),
 * 2. the EXACT keys of the reads that every write invalidates.
 */

const { registrarResultadoEncuentro } = vi.hoisted(() => ({
  registrarResultadoEncuentro: vi.fn(),
}));

vi.mock("../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance: vi.fn(),
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion: vi.fn(),
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro,
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const OTRA_COMPETENCIA_ID = "99999999-9999-4999-8999-999999999999";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const GANADOR_ID = "33333333-3333-4333-8333-333333333333";

function crearCliente() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function envoltorio(cliente: QueryClient) {
  return function Envoltorio({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={cliente}>{children}</QueryClientProvider>
    );
  };
}

describe("Los payloads de las comandos", () => {
  it("compone el horario con la fecha de la competencia", () => {
    const payload = construirPayloadProgramacion({
      competenciaId: COMPETENCIA_ID,
      encuentroId: ENCUENTRO_ID,
      expectedVersion: 3,
      datos: {
        fecha: "2026-10-25",
        hora_inicio: "10:00",
        hora_fin: "10:45",
        motivo: "Programacion del encuentro",
      },
    });

    expect(payload).toEqual({
      inicio_programado: "2026-10-25T10:00:00",
      fin_programado: "2026-10-25T10:45:00",
      motivo: "Programacion del encuentro",
      expected_version: 3,
    });
  });

  it("deja los puntajes en null cuando no hay marcador", () => {
    const payload = construirPayloadResultado({
      competenciaId: COMPETENCIA_ID,
      encuentroId: ENCUENTRO_ID,
      expectedVersion: 4,
      datos: {
        ganador_id: GANADOR_ID,
        puntaje_1: null,
        puntaje_2: null,
        marcador_detalle: "",
        motivo: "Registro del resultado",
      },
    });

    expect(payload).toEqual({
      ganador_id: GANADOR_ID,
      puntaje_1: null,
      puntaje_2: null,
      marcador_detalle: null,
      motivo: "Registro del resultado",
      expected_version: 4,
    });
  });

  it("manda el override SOLO cuando el impacto fue aceptado", () => {
    const sinAceptar = construirPayloadCorreccion({
      competenciaId: COMPETENCIA_ID,
      encuentroId: ENCUENTRO_ID,
      expectedVersion: 9,
      datos: {
        ganador_id: GANADOR_ID,
        motivo: "Correccion administrativa del ganador",
        acepta_impacto: false,
      },
    });

    const aceptado = construirPayloadCorreccion({
      competenciaId: COMPETENCIA_ID,
      encuentroId: ENCUENTRO_ID,
      expectedVersion: 9,
      datos: {
        ganador_id: GANADOR_ID,
        motivo: "Correccion administrativa del ganador",
        acepta_impacto: true,
      },
    });

    expect(sinAceptar.override).toBe(false);
    expect(sinAceptar.acepta_impacto).toBe(false);
    expect(aceptado.override).toBe(true);
    expect(aceptado.acepta_impacto).toBe(true);
    expect(aceptado.expected_version).toBe(9);
  });
});

describe("La invalidación de las lecturas", () => {
  it("invalida EXACTAMENTE las cuatro lecturas del módulo", async () => {
    const cliente = crearCliente();
    const espia = vi.spyOn(cliente, "invalidateQueries");

    await invalidarLecturasCompetencia(cliente, COMPETENCIA_ID);

    expect(espia).toHaveBeenCalledWith({
      queryKey: ["admin", "competencias", "detalle", COMPETENCIA_ID],
      exact: true,
    });
    expect(espia).toHaveBeenCalledWith({
      queryKey: ["admin", "competencias", "cuadro", COMPETENCIA_ID],
      exact: true,
    });
    expect(espia).toHaveBeenCalledWith({
      queryKey: ["admin", "competencias", "lista"],
      exact: false,
    });
    expect(espia).toHaveBeenCalledWith({
      queryKey: ["admin", "competencias", "agenda"],
      exact: false,
    });
  });

  it("NO invalida el detalle de OTRA competencia", async () => {
    const cliente = crearCliente();

    cliente.setQueryData(["admin", "competencias", "detalle", COMPETENCIA_ID], {
      success: true,
    });
    cliente.setQueryData(
      ["admin", "competencias", "detalle", OTRA_COMPETENCIA_ID],
      { success: true },
    );

    await invalidarLecturasCompetencia(cliente, COMPETENCIA_ID);

    expect(
      cliente.getQueryState([
        "admin",
        "competencias",
        "detalle",
        COMPETENCIA_ID,
      ])?.isInvalidated,
    ).toBe(true);
    expect(
      cliente.getQueryState([
        "admin",
        "competencias",
        "detalle",
        OTRA_COMPETENCIA_ID,
      ])?.isInvalidated,
    ).toBe(false);
  });
});

describe("La mutación del resultado", () => {
  it("manda el payload exacto y invalida las lecturas", async () => {
    const cliente = crearCliente();
    registrarResultadoEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });

    const { result } = renderHook(() => useRegistrarResultadoEncuentro(), {
      wrapper: envoltorio(cliente),
    });

    await result.current.mutateAsync({
      competenciaId: COMPETENCIA_ID,
      encuentroId: ENCUENTRO_ID,
      expectedVersion: 11,
      datos: {
        ganador_id: GANADOR_ID,
        puntaje_1: 3,
        puntaje_2: 1,
        marcador_detalle: "3 sets a 2",
        motivo: "Registro del resultado del encuentro",
      },
    });

    expect(registrarResultadoEncuentro).toHaveBeenCalledWith(ENCUENTRO_ID, {
      ganador_id: GANADOR_ID,
      puntaje_1: 3,
      puntaje_2: 1,
      marcador_detalle: "3 sets a 2",
      motivo: "Registro del resultado del encuentro",
      expected_version: 11,
    });
  });
});
