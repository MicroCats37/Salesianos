// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { configureToast } from "@/errors";
import { createQueryClient } from "@/lib/query-client";
import {
  clavesInscripcionDetalle,
  clavesInscripcionPool,
} from "../../utils/inscripcion.claves.utils";
import {
  useAgregarParticipante,
  useAltaInscripcion,
  useCompraCupos,
  useRetirarParticipante,
} from "../useInscripcionMutaciones";

/**
 * The contract of the writes of the registration area.
 *
 * The suite freezes THREE things for every write of the area:
 *
 * 1. the ROUTE that is called and the BODY that travels;
 * 2. the message of the SERVER when the write fails: the failure is shown
 *    with the words of the backend, never with an invented text;
 * 3. the INVALIDATION: the reads that the write dirties are invalidated even
 *    when the write FAILED (a 409 means that another actor changed the same
 *    registration and the screen has to be refreshed anyway).
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

const POOL = {
  inscripcion_id: "ins-1",
  cupos_pagados: 10,
  cupos_asignados: 0,
  cupos_disponibles: 10,
  participaciones: [],
  impedimentos: [],
  causa_operativa: "PARTICIPACION_AGREGADA",
};

const ALTA = {
  inscripcion: INSCRIPCION,
  compra: COMPRA,
  causa_operativa: "INSCRIPCION_CREADA",
};

const PAYLOAD_ALTA = {
  edicion_id: "ed-1",
  paquete_id: "paq-1",
  promocion_id: "pro-1",
  cantidad: 10,
  equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
};

/**
 * The failure of the server: the envelope of the error carries the words of
 * the backend and the field errors that the form needs.
 */
const ERROR_422 = {
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

function envelope(data: unknown, message: string | null = null) {
  return { success: true, data, error: null, message };
}

function crearWrapper(client: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client }, children);
  };
}

let client: ReturnType<typeof createQueryClient>;
let errores: string[];
let exitos: string[];

beforeEach(() => {
  apiSendMock.mockReset();
  client = createQueryClient();
  errores = [];
  exitos = [];
  configureToast(
    (mensaje) => {
      errores.push(mensaje);
    },
    (mensaje) => {
      exitos.push(mensaje);
    },
  );
});

describe("el alta de una inscripción", () => {
  it("viaja a POST /inscripciones con el payload exacto", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope(ALTA, "Inscripción registrada correctamente."),
    });

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync(PAYLOAD_ALTA);
    });

    expect(apiSendMock).toHaveBeenCalledWith(
      "post",
      "/inscripciones",
      PAYLOAD_ALTA,
    );
  });

  it("toma el mensaje del servidor como notificación de éxito", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope(ALTA, "Inscripción registrada correctamente."),
    });

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync(PAYLOAD_ALTA);
    });

    expect(exitos).toEqual(["Inscripción registrada correctamente."]);
    expect(errores).toEqual([]);
  });

  it("muestra el mensaje del servidor cuando la escritura falla", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync(PAYLOAD_ALTA).catch(() => undefined);
    });

    expect(errores).toEqual(["La solicitud no es válida."]);
    expect(exitos).toEqual([]);
  });

  it("propaga el error ORIGINAL: los errores de campo llegan al formulario", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    let recibido: unknown = null;

    await act(async () => {
      try {
        await result.current.mutateAsync(PAYLOAD_ALTA);
      } catch (error) {
        recibido = error;
      }
    });

    expect(recibido).toBe(ERROR_422);
  });

  it("invalida el detalle de las inscripciones AUNQUE la escritura falle", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    client.setQueryData(clavesInscripcionDetalle.detail("ins-1"), INSCRIPCION);

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync(PAYLOAD_ALTA).catch(() => undefined);
    });

    await waitFor(() =>
      expect(
        client.getQueryState(clavesInscripcionDetalle.detail("ins-1"))
          ?.isInvalidated,
      ).toBe(true),
    );
  });

  it("no crea la entrada de una inscripción que nadie leyó", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: envelope(ALTA) });

    const { result } = renderHook(() => useAltaInscripcion(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync(PAYLOAD_ALTA);
    });

    expect(
      client.getQueryData(clavesInscripcionDetalle.detail("ins-1")),
    ).toBeUndefined();
  });
});

describe("el pool de una inscripción", () => {
  it("agregar un participante viaja a la ruta del pool con el payload del servicio", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(POOL, "Participante agregado."),
    });

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
    expect(exitos).toEqual(["Participante agregado."]);
  });

  it("retirar un participante viaja a la ruta de la participación", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(POOL, "Participante retirado."),
    });

    const { result } = renderHook(() => useRetirarParticipante(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        inscripcion_id: "ins-1",
        participacion_id: "par-1",
      });
    });

    expect(apiSendMock).toHaveBeenCalledWith(
      "delete",
      "/inscripciones/ins-1/participantes/par-1",
    );
  });

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

    expect(
      client.getQueryData(clavesInscripcionPool.detail("ins-1")),
    ).toBeUndefined();
  });

  it("muestra el mensaje del servidor cuando la escritura del pool falla", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    const { result } = renderHook(() => useAgregarParticipante(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current
        .mutateAsync({
          inscripcion_id: "ins-1",
          payload: { equipo_id: "eq-1", persona_id: "per-9" },
        })
        .catch(() => undefined);
    });

    expect(errores).toEqual(["La solicitud no es válida."]);
  });

  it("invalida el detalle AUNQUE la escritura del pool falle", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    client.setQueryData(clavesInscripcionDetalle.detail("ins-1"), INSCRIPCION);

    const { result } = renderHook(() => useAgregarParticipante(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current
        .mutateAsync({
          inscripcion_id: "ins-1",
          payload: { equipo_id: "eq-1", persona_id: "per-9" },
        })
        .catch(() => undefined);
    });

    await waitFor(() =>
      expect(
        client.getQueryState(clavesInscripcionDetalle.detail("ins-1"))
          ?.isInvalidated,
      ).toBe(true),
    );
  });
});

describe("la compra de cupos", () => {
  it("viaja a POST /inscripciones/{id}/compras/cupos con el payload del servicio", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: envelope(
        {
          inscripcion_id: "ins-1",
          compra: COMPRA,
          cupos_solicitados: 3,
          cupos_pagados: 10,
          cupos_asignados: 0,
          cupos_disponibles: 10,
          causa_operativa: "COMPRA_CUPOS_CREADA",
        },
        "Cupos comprados.",
      ),
    });

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
    expect(exitos).toEqual(["Cupos comprados."]);
  });

  it("NO escribe el pool: la respuesta NO es un pool", async () => {
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

    expect(client.getQueryData(clavesInscripcionPool.detail("ins-1"))).toEqual(
      POOL,
    );
    expect(
      client.getQueryState(clavesInscripcionPool.detail("ins-1"))
        ?.isInvalidated,
    ).toBe(true);
  });

  it("invalida el pool y el detalle AUNQUE la compra falle", async () => {
    apiSendMock.mockRejectedValue(ERROR_422);

    client.setQueryData(clavesInscripcionPool.detail("ins-1"), POOL);
    client.setQueryData(clavesInscripcionDetalle.detail("ins-1"), INSCRIPCION);

    const { result } = renderHook(() => useCompraCupos(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current
        .mutateAsync({
          inscripcion_id: "ins-1",
          payload: { cantidad: 3 },
        })
        .catch(() => undefined);
    });

    await waitFor(() => {
      expect(
        client.getQueryState(clavesInscripcionPool.detail("ins-1"))
          ?.isInvalidated,
      ).toBe(true);
      expect(
        client.getQueryState(clavesInscripcionDetalle.detail("ins-1"))
          ?.isInvalidated,
      ).toBe(true);
    });

    expect(errores).toEqual(["La solicitud no es válida."]);
  });
});
