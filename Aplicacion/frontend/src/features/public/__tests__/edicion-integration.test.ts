import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiSend } from "@/lib/api";
import { EdicionActualSchema } from "../schemas/edicion.schema";
import {
  EDICION_ACTUAL_PATH,
  obtenerEdicionActual,
} from "../services/edicion.service";
import { edicionClaves } from "../utils/edicion.claves.utils";

/**
 * The integration of the current edition (`RT-ED-01`).
 *
 * The suite freezes THREE things and nothing else:
 *
 * 1. The Zod mirror is EXACT: it accepts the wrapper of the presenter and it
 *    rejects an answer that does not match it. An answer that does not match
 *    is a failure, never a partially trusted value.
 * 2. The route is the REGISTERED one (`GET /ediciones/actual`).
 * 3. The key carries the identity of the dataset, so one dataset is one
 *    namespace and one cache entry.
 */

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
  default: { get: vi.fn(), post: vi.fn() },
}));

const EDICION = {
  id: "11111111-1111-4111-8111-111111111111",
  created_at: "2026-11-19T00:00:00Z",
  updated_at: "2026-11-19T00:00:00Z",
  evento_id: "22222222-2222-4222-8222-222222222222",
  evento_nombre: "FEST",
  evento_slug: "fest",
  nombre: "EDICIÓN 2026",
  slug: "edicion-2026",
  anio: 2026,
  estado: "PUBLICADA",
  modulos_habilitados: ["inscripciones"],
  fecha_inicio: "2026-11-21",
  fecha_fin: "2026-11-22",
  modulos: [
    { clave: "inscripciones", nombre: "Inscripciones", habilitado: true },
    { clave: "pases", nombre: "Pases", habilitado: false },
  ],
};

function envelope(data: unknown) {
  return { success: true, data, error: null, message: null };
}

beforeEach(() => {
  vi.mocked(apiSend).mockReset();
});

describe("el espejo de la edición vigente", () => {
  it("acepta el wrapper exacto del presenter", () => {
    const edicion = EdicionActualSchema.parse(EDICION);

    expect(edicion.nombre).toBe("EDICIÓN 2026");
    expect(edicion.anio).toBe(2026);
    expect(edicion.modulos).toHaveLength(2);
    expect(edicion.modulos[1]?.habilitado).toBe(false);
  });

  it("rechaza un wrapper al que le falta un campo declarado", () => {
    const { modulos: _modulos, ...incompleta } = EDICION;

    expect(EdicionActualSchema.safeParse(incompleta).success).toBe(false);
  });

  it("rechaza un identificador que no es un identificador", () => {
    expect(
      EdicionActualSchema.safeParse({ ...EDICION, id: "no-es-un-uuid" })
        .success,
    ).toBe(false);
  });
});

describe("la ruta de la edición vigente", () => {
  it("usa la ruta registrada y devuelve el wrapper", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope(EDICION),
    });

    const edicion = await obtenerEdicionActual();

    expect(apiSend).toHaveBeenCalledWith("GET", EDICION_ACTUAL_PATH);
    expect(edicion.evento_nombre).toBe("FEST");
  });

  it("falla en voz alta cuando la respuesta no cumple el contrato", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope({ ...EDICION, anio: "2026" }),
    });

    await expect(obtenerEdicionActual()).rejects.toThrow();
  });

  it("nunca parsea un cuerpo vacío", async () => {
    vi.mocked(apiSend).mockResolvedValue({ status: 204, data: null });

    await expect(obtenerEdicionActual()).rejects.toThrow();
  });
});

describe("la clave de la edición vigente", () => {
  it("vive en un solo namespace y lleva la identidad del dataset", () => {
    expect(edicionClaves.todas).toEqual(["edicion"]);
    expect(edicionClaves.actual()).toEqual(["edicion", "actual"]);
  });
});
