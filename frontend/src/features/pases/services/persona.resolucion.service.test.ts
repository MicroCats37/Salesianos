// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The transport of the EXACT identity lookup of an existing `Persona`.
 *
 * The suite verifies the contract at the HTTP boundary: the exact URL, the
 * exact query parameters and the 1:1 Zod mirror of the answer.
 */

const { get } = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock("@/lib/api", () => ({
  api: { get },
  default: { get },
}));

import { resolverPersona } from "./persona.resolucion.service";

const PERSONA = {
  persona_id: "33333333-3333-4333-8333-333333333333",
  nombre_completo: "Ana Pérez",
  tipo_documento: "DNI",
  numero_documento: "12345678",
};

function envolver(data: unknown) {
  return { success: true, data, error: null, message: null };
}

describe("El servicio de resolución de persona", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockResolvedValue({ data: envolver(PERSONA) });
  });

  it("consulta el endpoint EXACTO con los parámetros normalizados", async () => {
    await resolverPersona("  dni ", " 12345678 ");

    expect(get).toHaveBeenCalledTimes(1);
    expect(get).toHaveBeenCalledWith("/personas/resolver", {
      params: {
        tipo_documento: "DNI",
        numero_documento: "12345678",
      },
    });
  });

  it("devuelve la persona resuelta tal cual la reporta el backend", async () => {
    const persona = await resolverPersona("DNI", "12345678");

    expect(persona).toEqual(PERSONA);
  });

  it("no inventa campos: la respuesta sólo tiene los cuatro declarados", async () => {
    const persona = await resolverPersona("DNI", "12345678");

    expect(Object.keys(persona).sort()).toEqual([
      "nombre_completo",
      "numero_documento",
      "persona_id",
      "tipo_documento",
    ]);
  });

  it("propaga el 404 del backend como error tipado", async () => {
    const { ApiQueryError } = await import("@/hooks/callsApi/useApiQuery");

    get.mockRejectedValue(
      new ApiQueryError(
        "No se encontró una persona registrada con ese documento.",
        404,
      ),
    );

    await expect(resolverPersona("DNI", "99999999")).rejects.toBeInstanceOf(
      ApiQueryError,
    );
  });

  it("rechaza una respuesta que NO cumple el contrato", async () => {
    get.mockResolvedValue({
      data: envolver({ persona_id: "x", email: "ana@example.com" }),
    });

    await expect(resolverPersona("DNI", "12345678")).rejects.toBeTruthy();
  });
});
