// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiSend } = vi.hoisted(() => ({ apiSend: vi.fn() }));

vi.mock("@/lib/api", () => ({
  apiSend,
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
}));

import {
  cuentaPartidosEnvelope,
  cuentaPartidosSchema,
} from "../schemas/cuenta-partidos.schema";
import { listarPartidosCuenta } from "../services/cuenta-partidos.service";
import { MisPartidosView } from "../views/MisPartidosView";

/**
 * "MIS PARTIDOS": el espejo, el cliente y los estados de la página.
 *
 * Change: `partidos-marcadores-competencias` · Batch 3B
 *
 * La suite congela CUATRO contratos:
 *
 * 1. el ESPEJO: la forma exacta del servidor y el rechazo de un cuerpo que
 *    no la cumple;
 * 2. la RUTA: el cliente llama a la ruta registrada y parsea el envelope;
 * 3. los ESTADOS: cargando, error y vacío;
 * 4. los CUBOS y la INVARIANTE: el ganador viaja como lo publicó el backend,
 *    nunca deducido del marcador.
 */

const EQUIPO_A = "55555555-5555-4555-8555-555555555555";
const EQUIPO_B = "77777777-7777-4777-8777-777777777777";

/** Un encuentro, exactamente como lo publica el backend. */
const ENCUENTRO = {
  id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  ronda_id: "22222222-2222-4222-8222-222222222222",
  ronda_etiqueta: "Cuartos de final",
  ronda_orden: 1,
  competencia_id: "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70",
  orden: 1,
  estado_publico: "FINALIZADO",
  es_bye: false,
  participantes: [
    {
      slot: "PARTICIPANTE_1",
      competencia_equipo_id: "44444444-4444-4444-8444-444444444444",
      equipo_id: EQUIPO_A,
      equipo_nombre: "Salesianos A",
      orden: 1,
    },
    {
      slot: "PARTICIPANTE_2",
      competencia_equipo_id: "66666666-6666-4666-8666-666666666666",
      equipo_id: EQUIPO_B,
      equipo_nombre: "Salesianos B",
      orden: 2,
    },
  ],
  inicio_programado: "2027-03-14T15:00:00Z",
  fin_programado: "2027-03-14T16:00:00Z",
  iniciado_en: "2027-03-14T15:02:00Z",
  finalizado_en: "2027-03-14T15:55:00Z",
  puntaje_1: 9,
  puntaje_2: 4,
  marcador_detalle: "Set 1: 9-4",
  ganador_equipo_id: EQUIPO_B,
  ganador_equipo_nombre: "Salesianos B",
  version: 7,
};

const PARTIDOS = {
  edicion_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  edicion_nombre: "Salesianos Fest 2027",
  total: 1,
  equipos: [
    {
      id: "44444444-4444-4444-8444-444444444444",
      equipo_id: EQUIPO_A,
      equipo_nombre: "Salesianos A",
      orden: 1,
      estado: "ACTIVO",
      version: 1,
    },
  ],
  en_vivo: [],
  proximos: [],
  finalizados: [ENCUENTRO],
};

function envelope(data: unknown) {
  return { success: true, data, error: null, message: null };
}

beforeEach(() => {
  apiSend.mockReset();
});

describe("el espejo de los partidos de la cuenta", () => {
  it("acepta la forma exacta de MisPartidosOut", () => {
    const resultado = cuentaPartidosSchema.parse(PARTIDOS);

    expect(resultado.total).toBe(1);
    expect(resultado.equipos[0].equipo_nombre).toBe("Salesianos A");
    expect(resultado.finalizados[0].ganador_equipo_id).toBe(EQUIPO_B);
    expect(resultado.finalizados[0].version).toBe(7);
  });

  it("acepta el envelope congelado", () => {
    const parseado = cuentaPartidosEnvelope.parse(envelope(PARTIDOS));

    expect(parseado.data?.total).toBe(1);
  });

  it("rechaza un cuerpo sin los tres cubos", () => {
    const { proximos: _proximos, ...sinCubos } = PARTIDOS;

    expect(() => cuentaPartidosSchema.parse(sinCubos)).toThrow();
  });

  it("rechaza un encuentro sin versión", () => {
    const { version: _version, ...sinVersion } = ENCUENTRO;

    expect(() =>
      cuentaPartidosSchema.parse({
        ...PARTIDOS,
        finalizados: [sinVersion],
      }),
    ).toThrow();
  });
});

describe("el cliente de los partidos de la cuenta", () => {
  it("llama a la ruta registrada y parsea el envelope", async () => {
    apiSend.mockResolvedValue({ status: 200, data: envelope(PARTIDOS) });

    const partidos = await listarPartidosCuenta();

    expect(partidos.total).toBe(1);
    expect(apiSend).toHaveBeenCalledWith("get", "/cuenta/mis-partidos");
  });

  it("un cuerpo que no cumple el contrato es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: envelope({ total: "muchos" }),
    });

    await expect(listarPartidosCuenta()).rejects.toThrow();
  });

  it("el 204 NUNCA se parsea", async () => {
    apiSend.mockResolvedValue({ status: 204, data: null });

    await expect(listarPartidosCuenta()).rejects.toThrow(/sin contenido/i);
  });
});

describe("la página de mis partidos", () => {
  it("espera al servidor mientras lee", () => {
    render(createElement(MisPartidosView, { estado: "cargando" }));

    expect(screen.getByText(/Cargando tus partidos/i)).toBeInTheDocument();
  });

  it("ofrece la acción que resuelve un error", () => {
    render(
      createElement(MisPartidosView, {
        estado: "error",
        mensajeError: "No se pudo leer el estado.",
      }),
    );

    expect(
      screen.getByText(/No pudimos cargar tus partidos/i),
    ).toBeInTheDocument();
    expect(screen.getByText("No se pudo leer el estado.")).toBeInTheDocument();
  });

  it("dice la verdad cuando la cuenta no tiene partidos", () => {
    render(
      createElement(MisPartidosView, {
        estado: "listo",
        partidos: {
          ...PARTIDOS,
          total: 0,
          equipos: [],
          finalizados: [],
        },
      }),
    );

    expect(
      screen.getByText(/Todavía no tienes partidos publicados/i),
    ).toBeInTheDocument();
  });

  it("muestra los TRES cubos con sus encabezados", () => {
    render(
      createElement(MisPartidosView, {
        estado: "listo",
        partidos: {
          ...PARTIDOS,
          total: 2,
          en_vivo: [{ ...ENCUENTRO, id: "aaa", estado_publico: "EN_VIVO" }],
          proximos: [{ ...ENCUENTRO, id: "bbb", estado_publico: "PROGRAMA" }],
        },
      }),
    );

    expect(
      screen.getByRole("heading", { name: /En vivo/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Próximos/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Últimos resultados/i }),
    ).toBeInTheDocument();
  });

  it("el ganador es el que publicó el backend, NO el que va ganando", () => {
    render(
      createElement(MisPartidosView, { estado: "listo", partidos: PARTIDOS }),
    );

    // El marcador es 9-4 y el ganador es Salesianos B.
    expect(screen.getByText("Ganó Salesianos B")).toBeInTheDocument();
    expect(screen.queryByText("Ganó Salesianos A")).not.toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("muestra los equipos de la cuenta", () => {
    render(
      createElement(MisPartidosView, { estado: "listo", partidos: PARTIDOS }),
    );

    // El nombre del equipo aparece en la lista de equipos y en el partido.
    expect(screen.getAllByText("Salesianos A").length).toBeGreaterThan(0);
  });
});
