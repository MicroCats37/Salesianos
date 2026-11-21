import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiSend } = vi.hoisted(() => ({ apiSend: vi.fn() }));

vi.mock("@/lib/api", () => ({
  apiSend,
  default: {
    get: vi.fn(),
    request: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

import {
  obtenerEncuentrosPublicos,
  RUTA_ENCUENTROS_PUBLICOS,
} from "../services/encuentro-publico.service";
import { ENCUENTROS_PUBLICOS } from "./datos.contract";

/**
 * The client of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * The suite proves the rules the interface depends on: the URL comes from the
 * REGISTERED controller, the body is parsed with the Zod mirror, a body that
 * does not comply is a LOUD failure and the `204` is never parsed.
 */
beforeEach(() => {
  apiSend.mockReset();
});

function envelope(data: unknown) {
  return {
    status: 200,
    data: { success: true, data, error: null, message: null },
  };
}

describe("el cliente de los encuentros públicos", () => {
  it("pide la ruta registrada y parsea el envelope con el espejo", async () => {
    apiSend.mockResolvedValue(envelope(ENCUENTROS_PUBLICOS));

    const encuentros = await obtenerEncuentrosPublicos();

    expect(encuentros.total).toBe(3);
    expect(encuentros.en_vivo).toHaveLength(1);
    expect(apiSend).toHaveBeenCalledWith(
      "get",
      "/publico/competencias/encuentros",
      undefined,
      expect.objectContaining({ params: undefined }),
    );
  });

  it("la ruta publicada es la del controller registrado", () => {
    expect(RUTA_ENCUENTROS_PUBLICOS).toBe("/publico/competencias/encuentros");
  });

  it("un cuerpo que no cumple el contrato es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue(envelope({ total: "muchos" }));

    await expect(obtenerEncuentrosPublicos()).rejects.toThrow();
  });

  it("un cuerpo sin los tres cubos es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue(envelope({ total: 3 }));

    await expect(obtenerEncuentrosPublicos()).rejects.toThrow();
  });

  it("el 204 NUNCA se parsea", async () => {
    apiSend.mockResolvedValue({ status: 204, data: null });

    await expect(obtenerEncuentrosPublicos()).rejects.toThrow(/sin contenido/i);
  });

  it("un envelope sin datos es un fallo, nunca un vacío silencioso", async () => {
    apiSend.mockResolvedValue({
      status: 200,
      data: { success: false, data: null, error: null, message: null },
    });

    await expect(obtenerEncuentrosPublicos()).rejects.toThrow();
  });
});
