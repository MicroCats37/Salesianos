// @vitest-environment jsdom

import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { configureToast } from "@/errors";
import { createQueryClient } from "@/lib/query-client";
import { useConfirmarTicket, usePreviewTicket } from "../useValidacion";

/**
 * The contract of the console of validation.
 *
 * The suite freezes FOUR things:
 *
 * 1. the ROUTE that is called and the BODY that travels: the credential
 *    travels in the body of the POST, never in the query string;
 * 2. the message of the SERVER when the operation fails;
 * 3. the answer that does not comply with the mirror is a FAILURE, never a
 *    partially trusted value;
 * 4. the credential is NEVER written in the cache: it is a secret and a cache
 *    would keep it in memory.
 *
 * The double lives at the TRANSPORT boundary (`apiSend`), not at the service
 * and not at the schema.
 */

const { apiSendMock } = vi.hoisted(() => ({ apiSendMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  api: { get: vi.fn(), post: vi.fn(), request: vi.fn() },
  apiSend: apiSendMock,
}));

const EDICION = "3f2504e0-4f89-41d3-9a0c-0305e82c3301";
const PERSONA = "6ba7b810-9dad-41d1-80b4-00c04fd430c8";
const USUARIO = "16fd2706-8baf-433b-82eb-8c7fada847da";

const PREVIEW = {
  edicion_id: EDICION,
  tipo_derecho: "PASE",
  codigo: "ABC123",
  estado: "ACTIVA",
  cantidad_total: 1,
  cantidad_disponible: 1,
  cantidad_consumida: 0,
  puede_canjear: true,
  motivo_codigo: null,
  motivo_mensaje: null,
  titular: { persona_id: PERSONA, nombre: "PERSONA DE EJEMPLO" },
};

const CONFIRMADO = {
  validacion_id: EDICION,
  tipo_derecho: "PASE",
  cantidad_consumida: 1,
  cantidad_restante: 0,
  estado: "CANJEADA",
  consumido_en: "2026-11-20T10:00:00+00:00",
  actor: { usuario_id: USUARIO, persona_id: null },
  repetido: false,
};

const ERROR_403 = {
  response: {
    status: 403,
    data: {
      success: false,
      data: null,
      error: {
        code: "SIN_PERMISO",
        message: "No tiene permiso para validar credenciales.",
        details: null,
        field_errors: null,
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

describe("la comprobación de una credencial", () => {
  it("viaja a POST /validaciones/preview con el código en el cuerpo", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(PREVIEW),
    });

    const { result } = renderHook(() => usePreviewTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync("ABC123");
    });

    expect(apiSendMock).toHaveBeenCalledWith("post", "/validaciones/preview", {
      codigo: "ABC123",
    });
  });

  it("devuelve la credencial que el servidor publica", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(PREVIEW),
    });

    const { result } = renderHook(() => usePreviewTicket(), {
      wrapper: crearWrapper(client),
    });

    let resultado: unknown = null;

    await act(async () => {
      resultado = await result.current.mutateAsync("ABC123");
    });

    expect(resultado).toEqual(PREVIEW);
  });

  it("NO escribe la credencial en la caché", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(PREVIEW),
    });

    const { result } = renderHook(() => usePreviewTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync("ABC123");
    });

    expect(client.getQueryCache().getAll()).toHaveLength(0);
  });

  it("muestra el mensaje del servidor cuando la comprobación falla", async () => {
    apiSendMock.mockRejectedValue(ERROR_403);

    const { result } = renderHook(() => usePreviewTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync("ABC123").catch(() => undefined);
    });

    expect(errores).toEqual(["No tiene permiso para validar credenciales."]);
  });

  it("es un fallo cuando la respuesta no cumple el contrato", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope({ ...PREVIEW, edicion_id: "no-es-un-uuid" }),
    });

    const { result } = renderHook(() => usePreviewTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync("ABC123").catch(() => undefined);
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe("el canje de una credencial", () => {
  it("viaja a POST /validaciones/confirmar con la clave de idempotencia", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(CONFIRMADO),
    });

    const { result } = renderHook(() => useConfirmarTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        codigo: "ABC123",
        idempotency_key: "validacion:ABC123:1",
      });
    });

    expect(apiSendMock).toHaveBeenCalledWith(
      "post",
      "/validaciones/confirmar",
      { codigo: "ABC123", idempotency_key: "validacion:ABC123:1" },
    );
  });

  it("devuelve el canje que el servidor publica", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(CONFIRMADO),
    });

    const { result } = renderHook(() => useConfirmarTicket(), {
      wrapper: crearWrapper(client),
    });

    let resultado: unknown = null;

    await act(async () => {
      resultado = await result.current.mutateAsync({
        codigo: "ABC123",
        idempotency_key: "validacion:ABC123:1",
      });
    });

    expect(resultado).toEqual(CONFIRMADO);
  });

  it("NO escribe el canje en la caché", async () => {
    apiSendMock.mockResolvedValue({
      status: 200,
      data: envelope(CONFIRMADO),
    });

    const { result } = renderHook(() => useConfirmarTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current.mutateAsync({
        codigo: "ABC123",
        idempotency_key: "validacion:ABC123:1",
      });
    });

    expect(client.getQueryCache().getAll()).toHaveLength(0);
  });

  it("muestra el mensaje del servidor cuando el canje falla", async () => {
    apiSendMock.mockRejectedValue(ERROR_403);

    const { result } = renderHook(() => useConfirmarTicket(), {
      wrapper: crearWrapper(client),
    });

    await act(async () => {
      await result.current
        .mutateAsync({
          codigo: "ABC123",
          idempotency_key: "validacion:ABC123:1",
        })
        .catch(() => undefined);
    });

    expect(errores).toEqual(["No tiene permiso para validar credenciales."]);
  });
});
