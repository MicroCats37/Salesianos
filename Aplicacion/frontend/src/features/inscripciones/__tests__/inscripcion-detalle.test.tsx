// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { PanelBeneficios } from "../components/PanelBeneficios";
import { PanelCompras } from "../components/PanelCompras";
import { PanelEquipos } from "../components/PanelEquipos";
import { PanelParticipantes } from "../components/PanelParticipantes";
import { PanelPool } from "../components/PanelPool";
import { MisInscripcionDetalleView } from "../views/MisInscripcionDetalleView";

/**
 * The states of ACCOUNT-03, the detail of a registration.
 *
 * The suite checks the two halves of the page: the states of the ROUTE
 * (the honest empty, the permission and the recoverable error) and the five
 * SECTIONS that the backend publishes (the balance of the cupos, the teams,
 * the people, the purchases and the benefits).
 *
 * The double lives at the TRANSPORT boundary, so the route, the envelope and
 * the cache are the ones of production. There is NO fixture of production in
 * this feature any more.
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

const INSCRIPCION = {
  id: "ins-1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  responsable_id: "per-1",
  paquete_id: "paq-1",
  paquete_nombre: "PAQUETE DE EJEMPLO",
  estado: "CREADA",
  referencia: "INSCRIPCION:ins-1:INICIAL",
  cupos_solicitados: 10,
  cupos_pagados: 8,
  cupos_asignados: 5,
  cupos_disponibles: 3,
  equipos: [
    {
      id: "eq-1",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      disciplina_id: "dis-1",
      disciplina_nombre: "FUTSAL",
      nombre: "EQUIPO DE EJEMPLO",
      estado: "ACTIVO",
    },
  ],
};

const POOL = {
  inscripcion_id: "ins-1",
  cupos_pagados: 8,
  cupos_asignados: 5,
  cupos_disponibles: 3,
  participaciones: [
    {
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
    },
  ],
  impedimentos: [
    {
      codigo: "EQUIPO_MAXIMO",
      mensaje: "Este equipo alcanzó el máximo de jugadores permitidos.",
      equipo_id: "eq-1",
    },
  ],
  causa_operativa: "POOL_CON_CUPOS_DISPONIBLES",
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

describe("ACCOUNT-03 - el detalle de la inscripción", () => {
  it("mientras el detalle viaja no inventa un balance", () => {
    apiSendMock.mockReturnValue(new Promise(() => undefined));

    render(<MisInscripcionDetalleView id="ins-1" />, {
      wrapper: crearWrapper(client),
    });

    expect(
      screen.getByText("No hay datos de esta inscripción todavía"),
    ).toBeDefined();
  });

  it("sin permiso lo explica y no parece un error", async () => {
    apiSendMock.mockRejectedValue({
      response: {
        status: 403,
        data: {
          success: false,
          data: null,
          error: {
            code: "INSCRIPCION_NO_AUTORIZADA",
            message: "La inscripción no pertenece a tu cuenta.",
            details: null,
            field_errors: null,
          },
          message: null,
        },
      },
    });

    render(<MisInscripcionDetalleView id="ins-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(
        screen.getByText("Tu cuenta no tiene acceso a esta inscripción"),
      ).toBeDefined(),
    );
  });

  it("con error ofrece reintentar, con el mensaje del servidor", async () => {
    apiSendMock.mockRejectedValue({
      response: {
        status: 503,
        data: {
          success: false,
          data: null,
          error: {
            code: "SERVICIO_NO_DISPONIBLE",
            message: "El servicio de inscripciones no está disponible.",
            details: null,
            field_errors: null,
          },
          message: null,
        },
      },
    });

    render(<MisInscripcionDetalleView id="ins-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(
        screen.getByText("El servicio de inscripciones no está disponible."),
      ).toBeDefined(),
    );

    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();
  });

  it("con datos muestra las cinco secciones y el balance del servidor", async () => {
    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url.endsWith("/pool")) {
        return Promise.resolve({ status: 200, data: envelope(POOL) });
      }
      return Promise.resolve({ status: 200, data: envelope(INSCRIPCION) });
    });

    render(<MisInscripcionDetalleView id="ins-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() => expect(screen.getByText("Cupos")).toBeDefined());

    expect(screen.getByText("Equipos")).toBeDefined();
    expect(screen.getByText("Personas")).toBeDefined();
    expect(screen.getByText("Compras")).toBeDefined();
    expect(screen.getByText("Beneficios")).toBeDefined();

    // El balance es el que publica el servidor: 8 pagados, 5 asignados y
    // 3 disponibles. La página no los resta.
    expect(screen.getByText("cupos pagados")).toBeDefined();
    expect(screen.getByText("cupos asignados")).toBeDefined();
    expect(screen.getByText("cupos disponibles")).toBeDefined();
    expect(
      screen.getByText("8 cupos pagados, 5 asignados y 3 disponibles."),
    ).toBeDefined();
  });
});

describe("ACCOUNT-03 - las cinco secciones", () => {
  it("el pool imprime el motivo del servidor tal cual", () => {
    render(<PanelPool pool={POOL} />);

    expect(
      screen.getByText(
        "Este equipo alcanzó el máximo de jugadores permitidos.",
      ),
    ).toBeDefined();
    expect(
      screen.getByText(/Causa de la respuesta: POOL_CON_CUPOS_DISPONIBLES/),
    ).toBeDefined();
  });

  it("los equipos muestran su disciplina y su estado", () => {
    render(<PanelEquipos equipos={INSCRIPCION.equipos} />);

    expect(screen.getByText("EQUIPO DE EJEMPLO")).toBeDefined();
    expect(screen.getByText("FUTSAL")).toBeDefined();
  });

  it("sin equipos la sección explica lo que no hay", () => {
    render(<PanelEquipos equipos={[]} />);

    expect(
      screen.getByText("Todavía no hay equipos en esta inscripción"),
    ).toBeDefined();
  });

  it("las personas se listan con el estado de su cupo", () => {
    render(<PanelParticipantes participaciones={POOL.participaciones} />);

    // La tabla y las tarjetas coexisten en el DOM: las dos muestran la misma
    // fila, asi que la asercion mira el conjunto y no un unico nodo.
    expect(screen.getAllByText("EQUIPO DE EJEMPLO").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ocupando cupo").length).toBeGreaterThan(0);
  });

  it("las compras son honestas: el servidor todavía no las publica", () => {
    render(<PanelCompras compras={null} />);

    expect(
      screen.getByText(
        "El servidor todavía no publica las compras de una inscripción",
      ),
    ).toBeDefined();
  });

  it("los beneficios concedidos son honestos mientras el servidor no los publica", () => {
    render(<PanelBeneficios beneficios={null} />);

    expect(
      screen.getByText("Los beneficios concedidos todavía no se publican"),
    ).toBeDefined();
  });
});
