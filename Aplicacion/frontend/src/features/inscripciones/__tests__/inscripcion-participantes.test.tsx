// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { SeccionParticipantes } from "../components/SeccionParticipantes";

/**
 * The management of the people of the pool (ACCOUNT-03).
 *
 * The suite freezes the two WRITES of the pool and the S-10 confirmation:
 *
 * - the assignment of a person travels by DOCUMENT and the SERVER resolves
 *   her (`RT-IN-05`);
 * - the withdrawal asks for a confirmation that names the effect and never
 *   promises a refund (`RT-IN-06`, `RN-I04`, `DEC-06`);
 * - the 422 of the server reaches the control that owns the field.
 */

const { apiSendMock } = vi.hoisted(() => ({ apiSendMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  api: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  apiSend: apiSendMock,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/mis-inscripciones/ins-1",
  useSearchParams: () => new URLSearchParams(),
}));

const EQUIPOS = [
  {
    id: "eq-1",
    created_at: "2026-11-19T10:00:00+00:00",
    updated_at: "2026-11-19T10:00:00+00:00",
    disciplina_id: "dis-1",
    disciplina_nombre: "FUTSAL",
    nombre: "EQUIPO DE EJEMPLO",
    estado: "ACTIVO",
  },
];

const PARTICIPACION = {
  id: "par-1",
  persona_id: "per-9",
  equipo_id: "eq-1",
  equipo_nombre: "EQUIPO DE EJEMPLO",
  disciplina_id: "dis-1",
  disciplina_nombre: "FUTSAL",
  rol: "JUGADOR",
  estado: "ACTIVA",
  ocupa_cupo: true,
  retirada_en: null,
};

const POOL = {
  inscripcion_id: "ins-1",
  cupos_pagados: 10,
  cupos_asignados: 1,
  cupos_disponibles: 9,
  participaciones: [PARTICIPACION],
  impedimentos: [],
  causa_operativa: "PARTICIPACION_AGREGADA",
};

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

function crearWrapper(client: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

let client: ReturnType<typeof createQueryClient>;

beforeEach(() => {
  apiSendMock.mockReset();
  client = createQueryClient();
});

describe("ACCOUNT-03 — las personas del pool", () => {
  it("asigna a la persona por documento y deja que el servidor la resuelva", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(POOL) });

    render(
      <SeccionParticipantes
        inscripcionId="ins-1"
        equipos={EQUIPOS}
        participaciones={[]}
      />,
      { wrapper: crearWrapper(client) },
    );

    const numero = screen.getByLabelText("Número de documento");
    fireEvent.change(numero, { target: { value: "12345678" } });

    const equipo = screen.getByLabelText("Equipo");
    fireEvent.change(equipo, { target: { value: "eq-1" } });

    fireEvent.click(
      screen.getByRole("button", { name: "Asignar al equipo" }),
    );

    await waitFor(() =>
      expect(apiSendMock).toHaveBeenCalledWith(
        "post",
        "/inscripciones/ins-1/participantes",
        {
          equipo_id: "eq-1",
          numero_documento: "12345678",
          tipo_documento: "DNI",
          rol: "JUGADOR",
        },
      ),
    );
  });

  it("la retirada pide confirmación y nombra el efecto", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(POOL) });

    render(
      <SeccionParticipantes
        inscripcionId="ins-1"
        equipos={EQUIPOS}
        participaciones={[PARTICIPACION]}
      />,
      { wrapper: crearWrapper(client) },
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Retirar" })[0]);

    await waitFor(() =>
      expect(
        screen.getByText("Retirar a esta persona del equipo"),
      ).toBeDefined(),
    );

    expect(
      screen.getByText(/no se devuelve dinero y el inventario no cambia/),
    ).toBeDefined();

    // Nada se envía hasta que la persona confirma.
    expect(apiSendMock).not.toHaveBeenCalled();
  });

  it("la retirada confirmada llama a la ruta de la participantación", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(POOL) });

    render(
      <SeccionParticipantes
        inscripcionId="ins-1"
        equipos={EQUIPOS}
        participaciones={[PARTICIPACION]}
      />,
      { wrapper: crearWrapper(client) },
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Retirar" })[0]);

    await waitFor(() =>
      expect(
        screen.getByText("Retirar a esta persona del equipo"),
      ).toBeDefined(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));

    await waitFor(() =>
      expect(apiSendMock).toHaveBeenCalledWith(
        "delete",
        "/inscripciones/ins-1/participantes/par-1",
      ),
    );
  });

  it("un 422 marca el control que posee el campo", async () => {
    apiSendMock.mockRejectedValue({
      response: {
        status: 422,
        data: {
          success: false,
          data: null,
          error: {
            code: "PARTICIPANTE_DUPLICADO",
            message: "La persona ya participa en esta inscripción.",
            details: null,
            field_errors: [
              {
                field: "numero_documento",
                code: "INVALID_VALUE",
                message: "La persona ya participa en esta inscripción.",
              },
            ],
          },
          message: null,
        },
      },
    });

    render(
      <SeccionParticipantes
        inscripcionId="ins-1"
        equipos={EQUIPOS}
        participaciones={[]}
      />,
      { wrapper: crearWrapper(client) },
    );

    const numero = screen.getByLabelText("Número de documento");
    fireEvent.change(numero, { target: { value: "12345678" } });

    const equipo = screen.getByLabelText("Equipo");
    fireEvent.change(equipo, { target: { value: "eq-1" } });

    fireEvent.click(screen.getByRole("button", { name: "Asignar al equipo" }));

    await waitFor(() =>
      expect(
        screen.getAllByText("La persona ya participa en esta inscripción.")
          .length,
      ).toBeGreaterThan(0),
    );
  });
});
