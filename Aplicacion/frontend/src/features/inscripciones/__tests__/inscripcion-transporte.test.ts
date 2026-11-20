// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import {
  useAgregarParticipante,
  useAltaInscripcion,
  useCompraCupos,
} from "../hooks/useInscripcionMutaciones";
import { useCatalogoPaquetes } from "../hooks/useCatalogo";
import { useInscripcionDetalle, useInscripcionPool } from "../hooks/useInscripcion";
import {
  clavesCatalogoPaquetes,
  clavesInscripcionDetalle,
  clavesInscripcionPool,
} from "../utils/inscripcion.claves.utils";

/**
 * The transport of the registration area.
 *
 * The suite freezes the CONTRACT of the transport: the exact route of every
 * call, the exact payload that travels, the exact invalidation that follows
 * a write and the exact behaviour of the 422.
 *
 * The double lives at the TRANSPORT boundary (`apiSend`), not at the service
 * and not at the schema: that way the URL, the payload and the cache policy
 * are all under test, and no production module carries a mock.
 */

const { apiSendMock } = vi.hoisted(() => ({ apiSendMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  api: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  apiSend: apiSendMock,
}));

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
      precio: {
        monto: "750.00",
        moneda: "PEN",
        vigente_desde: "2026-01-01",
        vigente_hasta: null,
      },
      beneficios: [],
      disciplinas: [],
    },
  ],
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

const POOL = {
  inscripcion_id: "ins-1",
  cupos_pagados: 10,
  cupos_asignados: 0,
  cupos_disponibles: 10,
  participaciones: [],
  impedimentos: [],
  causa_operativa: "PARTICIPACION_AGREGADA",
};

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

function crearWrapper(client: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client },
      children,
    );
  };
}

let client: ReturnType<typeof createQueryClient>;

beforeEach(() => {
  apiSendMock.mockReset();
  client = createQueryClient();
});

describe("API-02 — las rutas que se llaman", () => {
  it("el catálogo se lee en la ruta del backend objetivo, con la edición", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(CATALOGO),
    });

    const { result } = renderHook(
      () => useCatalogoPaquetes({ edicion_id: "ed-1" }),
      { wrapper: crearWrapper(client) },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiSendMock).toHaveBeenCalledWith("get", "/catalogo/paquetes", undefined, {
      params: { edicion_id: "ed-1" },
    });
  });

  it("la edición viaja en la clave, no sólo en la petición", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(CATALOGO) });

    const { result } = renderHook(
      () => useCatalogoPaquetes({ edicion_id: "ed-1" }),
      { wrapper: crearWrapper(client) },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(
      client.getQueryData(clavesCatalogoPaquetes.listPage({ edicion_id: "ed-1" })),
    ).toBeDefined();
    expect(
      client.getQueryData(clavesCatalogoPaquetes.listPage({})),
    ).toBeUndefined();
  });

  it("el detalle y el pool se leen en sus rutas", async () => {
    apiSendMock.mockImplementation((_metodo: string, url: string) => {
      if (url.endsWith("/pool")) {
        return Promise.resolve({ status: 200, data: envelope(POOL) });
      }
      return Promise.resolve({ status: 200, data: envelope(INSCRIPCION) });
    });

    const { result: detalle } = renderHook(() => useInscripcionDetalle("ins-1"), {
      wrapper: crearWrapper(client),
    });
    const { result: pool } = renderHook(() => useInscripcionPool("ins-1"), {
      wrapper: crearWrapper(client),
    });

    await waitFor(() => expect(detalle.current.isSuccess).toBe(true));
    await waitFor(() => expect(pool.current.isSuccess).toBe(true));

    expect(apiSendMock).toHaveBeenCalledWith("get", "/inscripciones/ins-1");
    expect(apiSendMock).toHaveBeenCalledWith("get", "/inscripciones/ins-1/pool");
  });

  it("NINGUNA llamada va a una ruta del backend congelado", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(CATALOGO) });

    const { result } = renderHook(() => useCatalogoPaquetes(), {
      wrapper: crearWrapper(client),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const urls = apiSendMock.mock.calls.map((llamada) => String(llamada[1]));

    for (const url of urls) {
      expect(url).not.toContain("/cotizaciones");
      expect(url).not.toContain("/inscripciones/completa");
      expect(url).not.toContain("/catalogo/promociones");
      expect(url).not.toContain("/catalogo/categorias");
    }
  });
});

describe("API-02 — el alta", () => {
  it("viaja a POST /inscripciones con el payload exacto", async () => {
    apiSendMock.mockResolvedValue({
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

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        edicion_id: "ed-1",
        paquete_id: "paq-1",
        equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
      });
    });

    expect(apiSendMock).toHaveBeenCalledWith("post", "/inscripciones", {
      edicion_id: "ed-1",
      paquete_id: "paq-1",
      equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
    });
  });

  it("no crea la entrada de una inscripción que nadie leyó", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope({
        inscripcion: INSCRIPCION,
        compra: COMPRA,
        causa_operativa: "INSCRIPCION_CREADA",
      }),
    });

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        edicion_id: "ed-1",
        paquete_id: "paq-1",
        equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
      });
    });

    expect(client.getQueryData(clavesInscripcionDetalle.detail("ins-1"))).toBeUndefined();
  });

  it("invalida el detalle de las inscripciones que ya estaban leídas", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope({
        inscripcion: INSCRIPCION,
        compra: COMPRA,
        causa_operativa: "INSCRIPCION_CREADA",
      }),
    });

    client.setQueryData(clavesInscripcionDetalle.detail("otra"), INSCRIPCION);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        edicion_id: "ed-1",
        paquete_id: "paq-1",
        equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
      });
    });

    expect(
      client.getQueryState(clavesInscripcionDetalle.detail("otra"))?.isInvalidated,
    ).toBe(true);
  });

  it("propaga el 422 ORIGINAL: los errores de campo llegan al formulario", async () => {
    const error422 = {
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
    };

    apiSendMock.mockRejectedValue(error422);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    let recibido: unknown = null;

    await act(async () => {
      try {
        await result.current.mutateAsync({
          edicion_id: "ed-1",
          paquete_id: "paq-1",
          equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
        });
      } catch (error) {
        recibido = error;
      }
    });

    // El error NO se envuelve: el `GenericForm` lee `error.field_errors` del
    // cuerpo crudo y marca el control que posee el campo.
    expect(recibido).toBe(error422);
  });

  it("un 409 no se reintenta solo: la carrera la decide el servidor", async () => {
    const error409 = {
      response: {
        status: 409,
        data: {
          success: false,
          data: null,
          error: {
            code: "PAQUETE_NO_VIGENTE",
            message: "El paquete ya no está vigente.",
            details: null,
            field_errors: null,
          },
          message: null,
        },
      },
    };

    apiSendMock.mockRejectedValue(error409);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current
        .mutateAsync({
          edicion_id: "ed-1",
          paquete_id: "paq-1",
          equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
        })
        .catch(() => undefined);
    });

    expect(apiSendMock).toHaveBeenCalledTimes(1);
  });
});

describe("API-02 — el pool", () => {
  it("agregar un participante ESCRIBE el pool que respondió el servidor", async () => {
    const poolNuevo = {
      ...POOL,
      cupos_asignados: 1,
      cupos_disponibles: 9,
      causa_operativa: "PARTICIPACION_AGREGADA",
    };

    apiSendMock.mockResolvedValue({ status: 200, data: envelope(poolNuevo) });

    client.setQueryData(clavesInscripcionPool.detail("ins-1"), POOL);

    const { result } = renderHook(() => useAgregarParticipante(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        inscripcion_id: "ins-1",
        payload: { equipo_id: "eq-1", persona_id: "per-9" },
      });
    });

    expect(apiSendMock).toHaveBeenCalledWith(
      "post",
      "/inscripciones/ins-1/participantes",
      { equipo_id: "eq-1", persona_id: "per-9" },
    );
    expect(client.getQueryData(clavesInscripcionPool.detail("ins-1"))).toEqual(
      poolNuevo,
    );
  });

  it("agregar un participante NO crea un pool que nadie leyó", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: envelope(POOL) });

    const { result } = renderHook(() => useAgregarParticipante(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        inscripcion_id: "ins-1",
        payload: { equipo_id: "eq-1", persona_id: "per-9" },
      });
    });

    expect(client.getQueryData(clavesInscripcionPool.detail("ins-1"))).toBeUndefined();
  });

  it("la compra de cupos NO escribe el pool: invalida y listo", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope({
        inscripcion_id: "ins-1",
        compra: COMPRA,
        cupos_solicitados: 3,
        cupos_pagados: 10,
        cupos_asignados: 0,
        cupos_disponibles: 10,
        causa_operativa: "COMPRA_CUPOS_CREADA",
      }),
    });

    client.setQueryData(clavesInscripcionPool.detail("ins-1"), POOL);

    const { result } = renderHook(() => useCompraCupos(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        inscripcion_id: "ins-1",
        payload: { cantidad: 3 },
      });
    });

    expect(apiSendMock).toHaveBeenCalledWith(
      "post",
      "/inscripciones/ins-1/compras/cupos",
      { cantidad: 3 },
    );
    // El pool NO se reescribe: la respuesta NO es un pool.
    expect(client.getQueryData(clavesInscripcionPool.detail("ins-1"))).toEqual(POOL);
    expect(
      client.getQueryState(clavesInscripcionPool.detail("ins-1"))?.isInvalidated,
    ).toBe(true);
  });
});
