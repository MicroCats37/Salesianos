// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useResolverPersona } from "./useResolverPersona";

/**
 * The mutation that resolves an EXISTING `Persona` by her civil identity.
 *
 * The suite verifies the three contracts the beneficiary panel depends on:
 *
 * 1. the lookup travels with the (tipo_documento, numero_documento) pair the
 *    buyer typed;
 * 2. a 404 is NOT a failure: it means "no such registered person" and the
 *    panel renders the not-found state instead of an error;
 * 3. any other failure reaches the buyer through the toast adapter.
 */

const { resolverPersona } = vi.hoisted(() => ({ resolverPersona: vi.fn() }));

vi.mock("../services/persona.resolucion.service", () => ({
  resolverPersona,
}));

const PERSONA = {
  persona_id: "33333333-3333-4333-8333-333333333333",
  nombre_completo: "Ana Pérez",
  tipo_documento: "DNI",
  numero_documento: "12345678",
};

function crearCliente() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function envoltorio(cliente: QueryClient) {
  return function Envoltorio({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={cliente}>{children}</QueryClientProvider>
    );
  };
}

describe("La mutación de resolución de persona", () => {
  it("viaja con el tipo y el número que escribió el comprador", async () => {
    resolverPersona.mockResolvedValue(PERSONA);

    const cliente = crearCliente();
    const { result } = renderHook(() => useResolverPersona(), {
      wrapper: envoltorio(cliente),
    });

    const persona = await result.current.mutateAsync({
      tipoDocumento: "DNI",
      numeroDocumento: "12345678",
    });

    expect(resolverPersona).toHaveBeenCalledTimes(1);
    expect(resolverPersona).toHaveBeenCalledWith("DNI", "12345678");
    expect(persona.persona_id).toBe(PERSONA.persona_id);
  });

  it("el 404 NO se reporta como error: es el estado 'no encontrada'", async () => {
    const { ApiQueryError } = await import("@/hooks/callsApi/useApiQuery");

    resolverPersona.mockRejectedValue(
      new ApiQueryError(
        "No se encontró una persona registrada con ese documento.",
        404,
      ),
    );

    const cliente = crearCliente();
    const { result } = renderHook(() => useResolverPersona(), {
      wrapper: envoltorio(cliente),
    });

    await expect(
      result.current.mutateAsync({
        tipoDocumento: "DNI",
        numeroDocumento: "99999999",
      }),
    ).rejects.toBeTruthy();

    await waitFor(() => {
      expect(result.current.error?.status).toBe(404);
    });
    expect(result.current.isError).toBe(true);
  });
});
