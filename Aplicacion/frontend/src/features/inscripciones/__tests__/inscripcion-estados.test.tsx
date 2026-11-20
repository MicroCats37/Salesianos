// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { InscripcionWizardView } from "../views/InscripcionWizardView";

/**
 * The states of SPORT-01, the wizard of a registration.
 *
 * The suite walks the states of `SH-03` on the wizard with the REAL
 * transport behind it: the double lives at `apiSend`, so the route, the
 * envelope and the cache are the ones of production.
 *
 * There is NO fixture of production in this feature any more: the examples
 * below are the JSON that the target backend answers with.
 */

const { apiSendMock } = vi.hoisted(() => ({ apiSendMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  api: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  apiSend: apiSendMock,
}));

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/inscripcion",
  useSearchParams: () => new URLSearchParams(),
}));

const DISCIPLINA = {
  id: "dis-1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  nombre: "FUTSAL",
  slug: "futsal",
  estado: "ACTIVA",
  modalidad: "MIXTO",
  minimo_por_equipo: 7,
  maximo_por_equipo: 10,
};

const CATALOGO = {
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  paquetes: [
    {
      id: "paq-1",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      edicion_id: "ed-1",
      edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
      nombre: "PAQUETE DE EJEMPLO",
      slug: "paquete-de-ejemplo",
      descripcion: "Paquete de ejemplo.",
      estado: "VIGENTE",
      cupos_incluidos: 10,
      minimo_compra_inicial: 7,
      precio: {
        monto: "750.00",
        moneda: "PEN",
        vigente_desde: "2026-01-01",
        vigente_hasta: null,
      },
      beneficios: [],
      disciplinas: [DISCIPLINA],
    },
  ],
};

const CATALOGO_PROMOCIONES = {
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  promociones: [
    {
      id: "pro-1",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      anio: 2012,
      nombre: "PROMOCIÓN 2012",
      estado: "ACTIVA",
    },
  ],
};

const CATALOGO_CATEGORIAS = {
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  categorias: [
    {
      id: "cat-1",
      created_at: "2026-11-19T10:00:00+00:00",
      updated_at: "2026-11-19T10:00:00+00:00",
      edicion_id: "ed-1",
      edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
      nombre: "JUNIOR",
      promocion_desde: 2012,
      promocion_hasta: 2025,
      estado: "ACTIVA",
    },
  ],
};

const COTIZACION = {
  paquete_id: "paq-1",
  paquete_nombre: "PAQUETE DE EJEMPLO",
  minimo_cantidad: 7,
  cantidad_cotizada: 7,
  precio_unitario: "750.00",
  total: "5250.00",
  moneda: "PEN",
  version: 2,
  estado: "ACTIVA",
  validez_hasta: "2026-11-21T10:00:00+00:00",
};

const INSCRIPCION = {
  id: "ins-1",
  created_at: "2026-11-19T10:00:00+00:00",
  updated_at: "2026-11-19T10:00:00+00:00",
  edicion_id: "ed-1",
  edicion_nombre: "EDICIÓN DE EJEMPLO 2026",
  responsable_id: "per-1",
  paquete_id: "paq-1",
  paquete_nombre: "PAQUETE DE EJEMPLO",
  promocion: { id: "pro-1", nombre: "PROMOCIÓN 2012", anio: 2012 },
  fusion_promocion: null,
  estado: "CREADA",
  referencia: "INSCRIPCION:ins-1:INICIAL",
  cupos_solicitados: 10,
  cupos_pagados: 0,
  cupos_asignados: 0,
  cupos_disponibles: 0,
  equipos: [],
};

const COMPRA = {
  compra_id: "cmp-1",
  orden_pago_id: "op-1",
  estado: "PENDIENTE",
  total: "750.00",
  moneda: "PEN",
  reutilizada: false,
};

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

/**
 * The answer of the server, routed by URL.
 *
 * The wizard reads FOUR datasets: the packages of the edition, the cohorts,
 * the competitive bands and the quotation of the selected package and the
 * selected quantity. The alta is the write.
 */
function responder(metodo: string, url: string) {
  if (url === "/cotizaciones") {
    return Promise.resolve({ status: 200, data: envelope(COTIZACION) });
  }

  if (metodo === "post") {
    return Promise.resolve({
      status: 201,
      data: envelope(
        {
          inscripcion: INSCRIPCION,
          compra: COMPRA,
          causa_operativa: "INSCRIPCION_CREADA",
        },
        "Inscripción registrada correctamente.",
      ),
    });
  }

  if (url === "/catalogo/promociones") {
    return Promise.resolve({
      status: 200,
      data: envelope(CATALOGO_PROMOCIONES),
    });
  }

  if (url === "/catalogo/categorias") {
    return Promise.resolve({
      status: 200,
      data: envelope(CATALOGO_CATEGORIAS),
    });
  }

  return Promise.resolve({ status: 200, data: envelope(CATALOGO) });
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
  replace.mockReset();
  client = createQueryClient();
});

describe("SPORT-01 — el asistente de la inscripción", () => {
  it("mientras el catálogo viaja no finge que no hay catálogo", () => {
    apiSendMock.mockReturnValue(new Promise(() => undefined));

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    expect(
      screen.getByText("Cargando los paquetes disponibles de la edición"),
    ).toBeDefined();
  });

  it("con catálogo ofrece los paquetes que publica el servidor", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) =>
      responder(metodo, url),
    );

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(screen.getByText("PAQUETE DE EJEMPLO")).toBeDefined(),
    );

    // El precio se imprime tal como lo manda el servidor: 750.00 PEN.
    expect(screen.getByText("750.00")).toBeDefined();
    expect(screen.getByText("PEN")).toBeDefined();
    // Y los cupos que otorga el paquete, declarados por el catálogo.
    expect(screen.getByText("10")).toBeDefined();
  });

  it("el error del catálogo es recuperable, con el mensaje del servidor", async () => {
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

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(
        screen.getByText("El servicio de inscripciones no está disponible."),
      ).toBeDefined(),
    );

    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();
  });

  it("recupera la operación pendiente en vez de crear otra", () => {
    render(
      <InscripcionWizardView
        pendiente={{
          inscripcion_id: "ins-1",
          compra: COMPRA,
          causa_operativa: "INSCRIPCION_CREADA",
        }}
      />,
      { wrapper: crearWrapper(client) },
    );

    expect(screen.getByText("Ya hay una inscripción en curso")).toBeDefined();
    expect(
      screen.getByText(/la inscripción no tiene ningún cupo disponible/),
    ).toBeDefined();
  });
});

describe("SPORT-01 — el alta", () => {
  /**
   * The wizard has FIVE steps: the package, the cohort, the teams, the
   * summary and the confirmation. The helper walks the first four.
   */
  async function llegarAlConfirmacion() {
    await waitFor(() =>
      expect(screen.getByText("PAQUETE DE EJEMPLO")).toBeDefined(),
    );

    fireEvent.click(screen.getByRole("radio", { name: /PAQUETE DE EJEMPLO/ }));

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    const promocion = await screen.findByLabelText("Tu promoción");
    fireEvent.change(promocion, { target: { value: "pro-1" } });

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    const disciplina = await screen.findByLabelText("Disciplina");
    fireEvent.change(disciplina, { target: { value: "dis-1" } });

    const nombre = screen.getByLabelText("Nombre del equipo");
    fireEvent.change(nombre, { target: { value: "Halcones" } });

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await waitFor(() =>
      expect(screen.getByText("Lo que vas a registrar")).toBeDefined(),
    );
  }

  it("el resumen dice que los cupos se habilitan al confirmar el pago", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) =>
      responder(metodo, url),
    );

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await llegarAlConfirmacion();

    expect(
      screen.getByText(/Se habilitan cuando el pago se confirme/),
    ).toBeDefined();
    expect(screen.getByText(/no tiene ningún cupo disponible/)).toBeDefined();
  });

  it("la cantidad arranca en el mínimo que DECLARA el paquete", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) =>
      responder(metodo, url),
    );

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(screen.getByText("PAQUETE DE EJEMPLO")).toBeDefined(),
    );

    fireEvent.click(screen.getByRole("radio", { name: /PAQUETE DE EJEMPLO/ }));

    await waitFor(() =>
      expect(screen.getByText(/exige un mínimo de 7 personas/)).toBeDefined(),
    );

    // El botón de DISMINUIR está apagado en el mínimo del paquete.
    const disminuir = screen.getByRole("button", {
      name: "Disminuir la cantidad de personas",
    });
    await waitFor(() => expect(disminuir).toHaveProperty("disabled", true));
  });

  it("la promoción es EXPLÍCITA: sin elegirla el asistente no avanza", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) =>
      responder(metodo, url),
    );

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await waitFor(() =>
      expect(screen.getByText("PAQUETE DE EJEMPLO")).toBeDefined(),
    );

    fireEvent.click(screen.getByRole("radio", { name: /PAQUETE DE EJEMPLO/ }));
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await screen.findByLabelText("Tu promoción");

    // Sin promoción no se avanza al paso de los equipos.
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await waitFor(() =>
      expect(screen.getByText("Elige tu promoción")).toBeDefined(),
    );
    expect(screen.queryByLabelText("Disciplina")).toBeNull();
  });

  it("el alta manda el payload exacto y publica el resultado del servidor", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) =>
      responder(metodo, url),
    );

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await llegarAlConfirmacion();

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await waitFor(() =>
      expect(screen.getAllByText("Qué pasa al confirmar")[0]).toBeDefined(),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Registrar la inscripción" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Inscripción registrada")).toBeDefined(),
    );

    const llamada = apiSendMock.mock.calls.find(
      (entrada) => entrada[1] === "/inscripciones",
    );
    const payload = llamada?.[2] as Record<string, unknown>;

    expect(payload).toMatchObject({
      edicion_id: "ed-1",
      paquete_id: "paq-1",
      promocion_id: "pro-1",
      cantidad: 7,
      equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
    });

    // El precio y el total NUNCA viajan: la verdad del dinero es del servidor.
    expect(payload).not.toHaveProperty("precio");
    expect(payload).not.toHaveProperty("precio_unitario");
    expect(payload).not.toHaveProperty("precio_unitario_cotizado");
    expect(payload).not.toHaveProperty("total");

    // Y la categoría tampoco: la deriva el servidor.
    expect(payload.equipos).toEqual([
      { disciplina_id: "dis-1", nombre: "Halcones" },
    ]);

    // La compra sigue PENDIENTE: el browser no dice que haya cupos.
    expect(screen.getByText(/Estado de la compra: PENDIENTE/)).toBeDefined();
  });

  it("un reintento NO crea una segunda inscripción: el servidor devuelve la misma", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) => {
      if (metodo === "post") {
        return Promise.resolve({
          status: 201,
          data: envelope({
            inscripcion: INSCRIPCION,
            compra: { ...COMPRA, reutilizada: true },
            causa_operativa: "INSCRIPCION_REUTILIZADA",
          }),
        });
      }
      return responder(metodo, url);
    });

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await llegarAlConfirmacion();

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await waitFor(() =>
      expect(screen.getAllByText("Qué pasa al confirmar")[0]).toBeDefined(),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Registrar la inscripción" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Ya existía esa inscripción")).toBeDefined(),
    );

    expect(
      screen.getByText(
        /no se ha creado una segunda ni se ha abierto otra compra/,
      ),
    ).toBeDefined();
  });

  it("un 422 deja el formulario intacto y muestra el error del campo", async () => {
    apiSendMock.mockImplementation((metodo: string, url: string) => {
      if (metodo === "post" && url === "/inscripciones") {
        return Promise.reject({
          response: {
            status: 422,
            data: {
              success: false,
              data: null,
              error: {
                code: "VALIDATION_ERROR",
                message: "La solicitud no es válida.",
                details: null,
                field_errors: [
                  {
                    field: "equipos.0.nombre",
                    code: "TOO_LONG",
                    message: "El nombre del equipo es demasiado largo.",
                  },
                ],
              },
              message: null,
            },
          },
        });
      }
      return responder(metodo, url);
    });

    render(<InscripcionWizardView edicionId="ed-1" />, {
      wrapper: crearWrapper(client),
    });

    await llegarAlConfirmacion();

    fireEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    await waitFor(() =>
      expect(screen.getAllByText("Qué pasa al confirmar")[0]).toBeDefined(),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Registrar la inscripción" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("No pudimos registrar la inscripción"),
      ).toBeDefined(),
    );

    // El error del campo viaja al control que lo posee: al volver al paso
    // de los equipos, el control muestra el mensaje del servidor. El paso de
    // los equipos es el TERCERO: primero está el de la promoción.
    fireEvent.click(screen.getByRole("button", { name: /Anterior/ }));
    fireEvent.click(screen.getByRole("button", { name: /Anterior/ }));
    fireEvent.click(screen.getByRole("button", { name: /Anterior/ }));

    await waitFor(() =>
      expect(
        screen.getByText("El nombre del equipo es demasiado largo."),
      ).toBeDefined(),
    );
  });
});
