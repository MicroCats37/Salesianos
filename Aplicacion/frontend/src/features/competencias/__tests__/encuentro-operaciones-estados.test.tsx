// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { AccionesEncuentro } from "../components/AccionesEncuentro";
import { claveEncuentrosPublicos } from "../publico/utils/encuentro-publico.claves.utils";
import type { Encuentro } from "../types/competencia.types";

/**
 * The operator surface of an encounter (`ADM-11`).
 *
 * The suite freezes the contracts that the operator depends on:
 *
 * 1. the ACTIONS come from the server: an action that `acciones` does not
 *    announce is not a button, and the transitions are NOT recreated here;
 * 2. a CONFLICT of version is EXPLAINED and nothing is written;
 * 3. the mutation invalidates the administration AND the public reads;
 * 4. the dialog is reachable with the keyboard and names its fields.
 */

const { apiSend } = vi.hoisted(() => ({ apiSend: vi.fn() }));

vi.mock("@/lib/api", () => ({
  apiSend,
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
}));

const COMPETENCIA = "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70";
const ENCUENTRO = "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80";

function encuentro(acciones: string[]): Encuentro {
  return {
    id: ENCUENTRO,
    ronda_id: "22222222-2222-4222-8222-222222222222",
    ronda_etiqueta: "Cuartos de final",
    ronda_orden: 1,
    competencia_id: COMPETENCIA,
    orden: 1,
    estado: "PROGRAMADO",
    es_bye: false,
    participantes: [
      {
        slot: "PARTICIPANTE_1",
        competencia_equipo_id: "44444444-4444-4444-8444-444444444444",
        equipo_id: "55555555-5555-4555-8555-555555555555",
        equipo_nombre: "Salesianos A",
        orden: 1,
      },
      {
        slot: "PARTICIPANTE_2",
        competencia_equipo_id: "66666666-6666-4666-8666-666666666666",
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
    iniciado_en: null,
    finalizado_en: null,
    version: 4,
    acciones,
  };
}

let client: ReturnType<typeof createQueryClient>;

function crearWrapper(queryClient: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

beforeEach(() => {
  apiSend.mockReset();
  client = createQueryClient();
});

describe("la superficie de operación del encuentro", () => {
  it("ofrece SOLO las acciones que el servidor anuncia", () => {
    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, {
          encuentro: encuentro(["registrar_resultado", "cancelar"]),
        }),
      ),
    );

    expect(
      screen.getByRole("button", { name: "Registrar el resultado" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancelar el encuentro" }),
    ).toBeInTheDocument();
    // El servidor NO anuncia estas acciones: no son botones.
    expect(
      screen.queryByRole("button", { name: "Programar" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Avanzar el ganador" }),
    ).not.toBeInTheDocument();
  });

  it("una acción que la superficie no ofrece se NOMBRA, no se esconde", () => {
    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, {
          encuentro: encuentro(["asignar_participantes"]),
        }),
      ),
    );

    expect(screen.getByText("Asignar participantes")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Asignar participantes" }),
    ).not.toBeInTheDocument();
  });

  it("en un estado terminal el servidor no admite cambios", () => {
    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, { encuentro: encuentro([]) }),
      ),
    );

    expect(
      screen.getByText(/En este estado el servidor no admite cambios/i),
    ).toBeInTheDocument();
  });

  it("el diálogo de un cambio de estado nombra su motivo y lo exige", () => {
    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, {
          encuentro: encuentro(["iniciar"]),
        }),
      ),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar el encuentro" }),
    );

    expect(
      screen.getByRole("heading", { name: "Iniciar el encuentro" }),
    ).toBeInTheDocument();
    // El motivo es un campo CON NOMBRE: el lector de pantalla lo anuncia.
    expect(screen.getByLabelText(/Motivo/i)).toBeInTheDocument();
  });

  it("un conflicto de versión se EXPLICA y no se reintenta a ciegas", async () => {
    const onConflicto = vi.fn();
    apiSend.mockRejectedValue(
      Object.assign(new Error("El recurso cambió mientras lo editabas."), {
        response: { status: 409, data: {} },
        isAxiosError: true,
      }),
    );

    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, {
          encuentro: encuentro(["iniciar"]),
          onConflicto,
        }),
      ),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar el encuentro" }),
    );
    fireEvent.change(screen.getByLabelText(/Motivo/i), {
      target: { value: "Inicio del encuentro" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(onConflicto).toHaveBeenCalled();
    });
    // NUNCA se reintenta: la petición se hace UNA vez.
    expect(apiSend).toHaveBeenCalledTimes(1);
    expect(apiSend.mock.calls[0][1]).toBe(
      `/competencias/${COMPETENCIA}/encuentros/${ENCUENTRO}`,
    );
  });

  it("la mutation invalida la administración Y la superficie pública", async () => {
    const espiar = vi.spyOn(client, "invalidateQueries");
    apiSend.mockResolvedValue({
      status: 200,
      data: {
        success: true,
        data: encuentro(["iniciar"]),
        error: null,
        message: "El encuentro se actualizó correctamente.",
      },
    });

    render(
      createElement(
        crearWrapper(client),
        null,
        createElement(AccionesEncuentro, {
          encuentro: encuentro(["iniciar"]),
        }),
      ),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar el encuentro" }),
    );
    fireEvent.change(screen.getByLabelText(/Motivo/i), {
      target: { value: "Inicio del encuentro" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(espiar).toHaveBeenCalled();
    });

    const invalidadas = espiar.mock.calls.map((llamada) => llamada[0]);
    const publica = invalidadas.find(
      (opciones) =>
        opciones &&
        JSON.stringify(opciones.queryKey) ===
          JSON.stringify(claveEncuentrosPublicos),
    );
    expect(publica).toBeDefined();
  });
});
