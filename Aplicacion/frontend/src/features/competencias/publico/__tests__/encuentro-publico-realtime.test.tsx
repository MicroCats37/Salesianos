// @vitest-environment jsdom

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEncuentrosPublicos } from "../hooks/useEncuentrosPublicos";
import { useEncuentrosPublicosRealtime } from "../hooks/useEncuentrosPublicosRealtime";
import { claveEncuentrosPublicos } from "../utils/encuentro-publico.claves.utils";

const { apiGet } = vi.hoisted(() => ({ apiGet: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: apiGet },
}));

class SocketDouble {
  static readonly OPEN = 1;
  static instances: SocketDouble[] = [];

  readyState = 0;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;

  constructor(readonly url: string) {
    SocketDouble.instances.push(this);
  }

  close() {
    this.readyState = 3;
  }

  open() {
    this.readyState = SocketDouble.OPEN;
    this.onopen?.();
  }

  receive(data: unknown) {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(data) }),
    );
  }
}

function wrapper(client: QueryClient) {
  return function QueryWrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

afterEach(() => {
  SocketDouble.instances = [];
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

beforeEach(() => {
  apiGet.mockReset();
});

describe("el realtime de encuentros públicos", () => {
  it("invalida al abrir y fuerza el refetch al recibir un evento válido", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.example.test/api");
    vi.stubGlobal("WebSocket", SocketDouble);
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const refetch = vi.spyOn(client, "refetchQueries");
    const { result } = renderHook(() => useEncuentrosPublicosRealtime(), {
      wrapper: wrapper(client),
    });

    const socket = SocketDouble.instances[0];
    expect(socket.url).toBe("wss://api.example.test/ws/encuentros/");

    await act(async () => socket.open());
    await waitFor(() => expect(result.current.estado).toBe("conectado"));
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: claveEncuentrosPublicos,
    });

    await act(async () => {
      socket.receive({
        type: "encuentro.actualizado",
        schema_version: 1,
        encuentro_id: "match-1",
        occurred_at: "2027-03-14T15:00:00.000000-05:00",
      });
    });

    await waitFor(() => expect(result.current.actualizadoEn).not.toBeNull());
    expect(result.current.actualizadoEn?.toISOString()).toBe(
      "2027-03-14T20:00:00.000Z",
    );
    expect(invalidate).toHaveBeenCalledTimes(1);
    expect(refetch).toHaveBeenCalledWith({
      queryKey: claveEncuentrosPublicos,
      type: "active",
    });
  });

  it("ignora eventos ajenos: HTTP sigue siendo la fuente de verdad", async () => {
    vi.stubGlobal("WebSocket", SocketDouble);
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    renderHook(() => useEncuentrosPublicosRealtime(), {
      wrapper: wrapper(client),
    });

    const socket = SocketDouble.instances[0];
    await act(async () => socket.open());
    await act(async () => socket.receive({ type: "desconocido" }));

    expect(invalidate).toHaveBeenCalledTimes(1);
  });

  it("vuelve a pedir el snapshot HTTP al recibir un evento válido", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.example.test/api");
    vi.stubGlobal("WebSocket", SocketDouble);
    apiGet.mockResolvedValue({
      data: {
        success: true,
        data: {
          ready: true,
          competitions: [],
          server_time: "2027-03-14T20:00:00.000Z",
          groups: [],
          knockout: [],
        },
      },
    });
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { result } = renderHook(
      () => ({
        snapshot: useEncuentrosPublicos(),
        realtime: useEncuentrosPublicosRealtime(),
      }),
      { wrapper: wrapper(client) },
    );

    await waitFor(() => expect(result.current.snapshot.isSuccess).toBe(true));
    expect(apiGet).toHaveBeenCalledTimes(1);

    const socket = SocketDouble.instances[0];
    await act(async () => socket.open());
    await waitFor(() => expect(apiGet).toHaveBeenCalledTimes(2));
    apiGet.mockClear();

    await act(async () => {
      socket.receive({
        type: "encuentro.actualizado",
        schema_version: 1,
        encuentro_id: "match-1",
        occurred_at: "2027-03-14T15:00:00.000000-05:00",
      });
    });

    await waitFor(() => expect(apiGet).toHaveBeenCalledTimes(1));
  });
});
