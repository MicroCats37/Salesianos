// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  type AnchorHTMLAttributes,
  createElement,
  type ReactNode,
} from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { clavesCompetencias } from "../utils/competencias.claves.utils";
import { CompetenciasListaRuta } from "../views/CompetenciasListaRuta";

/**
 * The transport of the list of competitions (`ADM-10`).
 *
 * The double lives at the TRANSPORT boundary (`apiSend`), not at the service
 * and not at the schema: that way the URL, the parameters and the envelope
 * are all under test, and no production module carries a mock.
 *
 * The suite freezes FOUR contracts:
 *
 * 1. the ROUTE and the PARAMETERS of the read;
 * 2. the ENVELOPE: an answer that does not match the mirror is a FAILURE;
 * 3. the REUSE of the canonical catalogue of the bands (one endpoint, one
 *    client, one key namespace);
 * 4. the STATES: a permission answer is not a recoverable error.
 */

const { apiSendMock } = vi.hoisted(() => ({ apiSendMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  api: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  apiSend: apiSendMock,
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) =>
    createElement("a", { href, ...props }, children),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/competencias",
}));

/** One row of the list, exactly as the presenter publishes it. */
const COMPETENCIA = {
  id: "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70",
  edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  disciplina_id: "1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  disciplina_nombre: "Fútbol 7",
  categoria_id: "8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81",
  categoria_nombre: "JUNIOR",
  nombre: "Copa Salesianos",
  estado: "PLANIFICADA",
  fecha: "2026-11-21",
  total_equipos: 8,
  total_encuentros: 7,
  total_encuentros_finalizados: 0,
};

/** The catalogue of the bands, exactly as the catalogue publishes it. */
const CATALOGO_CATEGORIAS = {
  edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  categorias: [
    {
      id: "8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
      edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
      nombre: "JUNIOR",
      promocion_desde: 2012,
      promocion_hasta: 2025,
      estado: "ACTIVA",
    },
  ],
};

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

/** Answers the two routes of the route with the wire of the presenters. */
function responderConAmbas() {
  apiSendMock.mockImplementation((_metodo: string, url: string) => {
    if (url === "/catalogo/categorias") {
      return Promise.resolve({
        status: 200,
        data: envelope(CATALOGO_CATEGORIAS),
      });
    }

    return Promise.resolve({
      status: 200,
      data: envelope([COMPETENCIA]),
    });
  });
}

function crearWrapper(client: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client }, children);
  };
}

let client: ReturnType<typeof createQueryClient>;

beforeEach(() => {
  apiSendMock.mockReset();
  client = createQueryClient();

  /**
   * El cliente de PRODUCCIÓN repite un fallo que no trae código HTTP (dos
   * intentos). La suite mide el ESTADO de la superficie, no la política de
   * reintento del cliente: sin este ajuste el error tarda y la aserción
   * sería temporal.
   */
  client.setDefaultOptions({ queries: { retry: false } });
});

describe("ADM-10 — la ruta que se llama", () => {
  it("la lista se lee en GET /competencias con los filtros de la URL", async () => {
    responderConAmbas();

    render(
      <CompetenciasListaRuta
        filtroEstado="PLANIFICADA"
        filtroCategoria="8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81"
      />,
      { wrapper: crearWrapper(client) },
    );

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    expect(apiSendMock).toHaveBeenCalledWith(
      "get",
      "/competencias",
      undefined,
      {
        params: {
          categoria_id: "8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81",
          estado: "PLANIFICADA",
        },
      },
    );
  });

  it("sin filtros la petición NO lleva query string", async () => {
    responderConAmbas();

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    expect(apiSendMock).toHaveBeenCalledWith(
      "get",
      "/competencias",
      undefined,
      {
        params: {},
      },
    );
  });

  it("los filtros viajan en la clave, no sólo en la petición", async () => {
    responderConAmbas();

    render(
      <CompetenciasListaRuta
        filtroEstado="PLANIFICADA"
        filtroCategoria="8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81"
      />,
      { wrapper: crearWrapper(client) },
    );

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    expect(
      client.getQueryData(
        clavesCompetencias.listPage({
          estado: "PLANIFICADA",
          categoria_id: "8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81",
        }),
      ),
    ).toBeDefined();
    expect(
      client.getQueryData(clavesCompetencias.listPage({})),
    ).toBeUndefined();
  });

  it("el catálogo de las bandas se lee con el cliente CANÓNICO", async () => {
    responderConAmbas();

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    // Un endpoint, un cliente: esta ruta NO declara un segundo cliente del
    // catálogo (FND-08, regla 1).
    expect(apiSendMock).toHaveBeenCalledWith(
      "get",
      "/catalogo/categorias",
      undefined,
      { params: undefined },
    );

    // Y las opciones del filtro son las que declara el catálogo.
    await waitFor(() =>
      expect(screen.getByLabelText("Categoría")).toBeInTheDocument(),
    );

    expect(
      screen
        .getByLabelText("Categoría")
        .querySelector("option[value='8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81']"),
    ).not.toBeNull();
  });

  it("NINGUNA llamada va a una ruta del backend congelado", async () => {
    responderConAmbas();

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    const urls = apiSendMock.mock.calls.map((llamada) => String(llamada[1]));

    for (const url of urls) {
      // El backend congelado publicaba el catálogo con barra final.
      expect(url).not.toContain("/catalogo/categorias/");
      expect(url).not.toContain("/competencias/");
    }
  });
});

describe("ADM-10 — el espejo del sobre", () => {
  it("una respuesta que NO cumple el espejo es un fallo, no una lista a medias", async () => {
    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url === "/catalogo/categorias") {
        return Promise.resolve({
          status: 200,
          data: envelope(CATALOGO_CATEGORIAS),
        });
      }

      // La fila sin `categoria_nombre`: el espejo la rechaza.
      const { categoria_nombre: _ausente, ...filaIncompleta } = COMPETENCIA;

      return Promise.resolve({
        status: 200,
        data: envelope([filaIncompleta]),
      });
    });

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(
        screen.getByText("No pudimos cargar las competencias"),
      ).toBeInTheDocument(),
    );

    expect(screen.queryByText("Copa Salesianos")).not.toBeInTheDocument();
  });

  it("un 204 es un fallo: un cuerpo vacío nunca se parsea", async () => {
    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url === "/catalogo/categorias") {
        return Promise.resolve({
          status: 200,
          data: envelope(CATALOGO_CATEGORIAS),
        });
      }

      return Promise.resolve({ status: 204, data: null });
    });

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(
        screen.getByText("No pudimos cargar las competencias"),
      ).toBeInTheDocument(),
    );
  });

  it("un 403 es un permiso, no un error recuperable", async () => {
    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url === "/catalogo/categorias") {
        return Promise.resolve({
          status: 200,
          data: envelope(CATALOGO_CATEGORIAS),
        });
      }

      return Promise.reject({
        response: {
          status: 403,
          data: {
            success: false,
            data: null,
            error: {
              code: "ACTION_NOT_ALLOWED",
              message: "Tu cuenta no puede leer las competencias.",
            },
            message: null,
          },
        },
      });
    });

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(
        screen.getByText(/No tienes permiso para ver esta sección/),
      ).toBeInTheDocument(),
    );

    expect(
      screen.queryByText("No pudimos cargar las competencias"),
    ).not.toBeInTheDocument();
  });
});

describe("ADM-10 — la acción que resuelve el error", () => {
  it("reintentar vuelve a leer la lista", async () => {
    let intentos = 0;

    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url === "/catalogo/categorias") {
        return Promise.resolve({
          status: 200,
          data: envelope(CATALOGO_CATEGORIAS),
        });
      }

      intentos += 1;

      if (intentos === 1) {
        return Promise.reject({
          response: {
            status: 500,
            data: {
              success: false,
              data: null,
              error: {
                code: "INTERNAL_ERROR",
                message: "Ocurrió un error inesperado.",
              },
              message: null,
            },
          },
        });
      }

      return Promise.resolve({
        status: 200,
        data: envelope([COMPETENCIA]),
      });
    });

    render(<CompetenciasListaRuta />, { wrapper: crearWrapper(client) });

    await waitFor(() =>
      expect(
        screen.getByText("No pudimos cargar las competencias"),
      ).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: /reintentar/i }));

    await waitFor(() =>
      expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0),
    );

    expect(intentos).toBe(2);
  });
});
