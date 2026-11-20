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
  comprarPase,
  ErrorContratoPase,
  listarPases,
  obtenerCompra,
} from "../services/pase.service";
import { paseClaves } from "../utils/pase.claves.utils";
import {
  aCampoDeFormulario,
  adaptarErrorDeCampos,
} from "../utils/pase.error.utils";
import {
  aPayloadAsignarBeneficiario,
  aPayloadComprarPase,
} from "../utils/pase.payload.utils";

/**
 * The wire of the pass domain.
 *
 * The suite proves the rules that the interface depends on: the URL comes
 * from the REGISTERED controller, the body is parsed with the Zod mirror, a
 * body that does not comply is a LOUD failure, the `204` is never parsed and
 * the credential travels in the header and never in the query string.
 */
const CATALOGO = {
  edicion_id: "00000000-0000-4000-8000-000000000001",
  edicion_nombre: "EDICION DE EJEMPLO",
  pases: [],
};

/**
 * The answer of the read of a purchase (`PaseCompraDetalleOut`).
 *
 * It is NOT the catalogue: every read is parsed with the mirror of the
 * wrapper it publishes, and a body of another shape is a loud failure.
 */
const COMPRA = {
  compra_pase_id: "00000000-0000-4000-8000-0000000000e1",
  estado: "PENDIENTE",
  cantidad: 2,
  asignados: 0,
  disponibles: 2,
  beneficiarios: [],
  compra_id: null,
  orden_pago_id: null,
  pase_id: "00000000-0000-4000-8000-0000000000c1",
  pase_nombre: "Pase general",
  edicion_nombre: "EDICION DE EJEMPLO",
  precio_unitario: 0,
  total: 0,
  moneda: "PEN",
  causa_operativa: "COMPRA_CREADA",
};

beforeEach(() => {
  apiSend.mockReset();
});

function envelope(data: unknown) {
  return {
    status: 200,
    data: { success: true, data, error: null, message: null },
  };
}
describe("el cliente del pase", () => {
  it("el catálogo se pide a la ruta registrada y se parsea con el espejo", async () => {
    apiSend.mockResolvedValue(envelope(CATALOGO));

    const catalogo = await listarPases();

    expect(catalogo.edicion_nombre).toBe("EDICION DE EJEMPLO");
    expect(apiSend).toHaveBeenCalledWith(
      "get",
      "/pases",
      undefined,
      expect.objectContaining({ params: undefined }),
    );
  });

  it("un cuerpo que no cumple el contrato es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue(envelope({ pases: "no-es-una-lista" }));

    await expect(listarPases()).rejects.toBeInstanceOf(ErrorContratoPase);
  });

  it("un 204 nunca se parsea", async () => {
    apiSend.mockResolvedValue({ status: 204, data: null });

    await expect(listarPases()).rejects.toBeInstanceOf(ErrorContratoPase);
  });

  it("la lectura de la compra viaja con el token en la cabecera", async () => {
    apiSend.mockResolvedValue(envelope(COMPRA));

    await obtenerCompra("00000000-0000-4000-8000-0000000000e1", "secreto");

    const [, url, , config] = apiSend.mock.calls[0];
    expect(url).toBe("/pases/compras/00000000-0000-4000-8000-0000000000e1");
    expect(config.headers).toEqual({ "X-Pase-Token": "secreto" });
    expect(config.params).toBeUndefined();
  });

  it("el token nunca viaja en la query string", async () => {
    apiSend.mockResolvedValue(envelope(COMPRA));

    await obtenerCompra("00000000-0000-4000-8000-0000000000e1", "secreto");

    const [, url] = apiSend.mock.calls[0];
    expect(String(url)).not.toContain("secreto");
    expect(String(url)).not.toContain("?");
  });
});
describe("el payload de la compra", () => {
  it("no lleva importe: el precio lo resuelve el servidor", () => {
    const payload = aPayloadComprarPase({
      pase_id: "00000000-0000-4000-8000-0000000000c1",
      cantidad: 2,
      datos: {
        tipoDocumento: "DNI",
        numeroDocumento: "12345678",
        nombres: "PERSONA",
        apellidos: "DE EJEMPLO",
        contactoEmail: "",
      },
    });

    expect(payload).toEqual({
      pase_id: "00000000-0000-4000-8000-0000000000c1",
      cantidad: 2,
      tipo_documento: "DNI",
      numero_documento: "12345678",
      nombres: "PERSONA",
      apellidos: "DE EJEMPLO",
      contacto_email: "",
    });
    expect(Object.keys(payload)).not.toContain("precio");
    expect(Object.keys(payload)).not.toContain("total");
  });

  it("la asignación omite el identificador de persona que no conoce", () => {
    const payload = aPayloadAsignarBeneficiario({
      tipoDocumento: "DNI",
      numeroDocumento: "12345678",
      nombres: "PERSONA",
      apellidos: "DE EJEMPLO",
      motivo: "",
    });

    expect(payload.persona_id).toBeUndefined();
    expect(payload.tipo_documento).toBe("DNI");
    expect(payload.numero_documento).toBe("12345678");
  });
});

describe("los errores de campo del servidor", () => {
  it("el nombre del wire llega al nombre del control", () => {
    expect(aCampoDeFormulario("numero_documento")).toBe("numeroDocumento");
    expect(aCampoDeFormulario("nombres")).toBe("nombres");
  });

  it("la adaptación conserva el status, el código y el mensaje", () => {
    const original = {
      response: {
        status: 422,
        data: {
          success: false,
          error: {
            code: "CAMPO_INVALIDO",
            message: "Revisa el documento.",
            field_errors: [
              {
                field: "numero_documento",
                code: "INVALIDO",
                message: "No es válido.",
              },
            ],
          },
        },
      },
    };

    const adaptado = adaptarErrorDeCampos(original) as typeof original;

    expect(adaptado.response.status).toBe(422);
    expect(adaptado.response.data.error.code).toBe("CAMPO_INVALIDO");
    expect(adaptado.response.data.error.message).toBe("Revisa el documento.");
    expect(adaptado.response.data.error.field_errors[0].field).toBe(
      "numeroDocumento",
    );
  });

  it("un error sin errores de campo viaja untouched", () => {
    const original = { response: { status: 500, data: { error: {} } } };

    expect(adaptarErrorDeCampos(original)).toBe(original);
  });
});

describe("las claves del pase", () => {
  it("la edición viaja en la clave del catálogo", () => {
    expect(paseClaves.catalogoParams({ edicion_id: "ed-1" })).toEqual([
      "pase",
      "catalogo",
      { edicion_id: "ed-1" },
    ]);
  });

  it("una edición ausente es la misma entrada que ninguna", () => {
    expect(paseClaves.catalogoParams()).toEqual(["pase", "catalogo"]);
    expect(paseClaves.catalogoParams({ edicion_id: undefined })).toEqual([
      "pase",
      "catalogo",
    ]);
  });

  it("la compra y sus beneficiarios viven bajo la misma compra", () => {
    expect(paseClaves.compra("e1")).toEqual(["pase", "compras", "e1"]);
    expect(paseClaves.beneficiarios("e1")).toEqual([
      "pase",
      "compras",
      "e1",
      "beneficiarios",
    ]);
  });
});
