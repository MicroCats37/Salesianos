import { describe, expect, it, vi } from "vitest";
import {
  ErrorAdmin,
  RUTAS_ADMIN,
  urlDeRutaAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { apiSend } from "@/lib/api";
import {
  compraParaClienteFormSchema,
  cotizacionPaseClienteSchema,
  evidenciaPagoCompraPaseSchema,
} from "../schemas/asistido.schema";
import {
  comprarPaseCliente,
  comprarPedidoCliente,
  cotizarPaseCliente,
} from "../services/asistido.service";
import {
  erroresDeCampoDeLaCompra,
  esPrecioCambiado,
} from "../utils/asistido.errores.utils";

/**
 * The PAID purchase of a pass, from the wire.
 *
 * The suite freezes the FOUR things that the paid purchase must NEVER do:
 *
 * 1. compute a price or a total in the browser;
 * 2. send a price or a total to the server;
 * 3. turn the DECLARED amount into the total of the purchase;
 * 4. accept an amount that is not a decimal with at most two decimals.
 */

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

const apiSendMock = vi.mocked(apiSend);

/** The quotation the server publishes. */
const COTIZACION = {
  success: true,
  data: {
    pase_id: "pase-1",
    edicion_id: "edicion-1",
    pase_nombre: "Pase FEST",
    cantidad: 2,
    precio_unitario: "35.00",
    total: "70.00",
    moneda: "PEN",
    version: "9f2c1a7b4d5e6f80",
    estado: "ACTIVA",
    validez_hasta: "2026-11-21T23:00:00Z",
  },
  error: null,
  message: "Cotización calculada correctamente.",
};

/** The purchase the server registers. */
const COMPRA = {
  success: true,
  data: {
    compra_id: "compra-1",
    recurso_id: "recurso-1",
    orden_pago_id: "orden-1",
    tipo: "PASE",
    concepto: "Pase FEST",
    total: "70.00",
    moneda: "PEN",
    estado: "PAGADA",
    estado_pago: "MANUAL",
    comprador_persona_id: "persona-cliente",
    comprador_nombre: "Rosa Díaz",
    cantidad: 2,
    monto_declarado: "60.00",
  },
  error: null,
  message: "La compra de pases para el cliente se registró correctamente.",
};

/** The client the command declares. */
const CLIENTE = {
  tipo_documento: "DNI",
  numero_documento: "77777777",
  nombres: "Rosa",
  apellidos: "Díaz",
  genero: "F",
  contacto_email: "rosa@example.com",
};

describe("ACP — la cotización del pase", () => {
  it("la ruta está registrada y declara su verdad", () => {
    const ruta = RUTAS_ADMIN.cotizarPaseCliente;

    expect(ruta.registrado).toBe(true);
    expect(ruta.ledger).toBeTruthy();
    expect(ruta.presentador).toBeTruthy();
    expect(ruta.wrapper).toBeTruthy();
    expect(ruta.motivo).toBeTruthy();
    expect(ruta.permiso).toBeTruthy();
    expect(urlDeRutaAdmin(ruta)).toBe("/administracion/pases/cotizacion");
  });

  it("el comando viaja con el pase y la cantidad, y NUNCA con un precio", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: COTIZACION });

    const resultado = await cotizarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
    });

    expect(resultado.total).toBe("70.00");
    expect(resultado.precio_unitario).toBe("35.00");
    expect(resultado.version).toBe("9f2c1a7b4d5e6f80");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      Record<string, unknown>,
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/pases/cotizacion");
    expect(cuerpo).toEqual({ pase_id: "pase-1", cantidad: 2 });
    expect(Object.keys(cuerpo)).not.toContain("precio");
    expect(Object.keys(cuerpo)).not.toContain("total");
  });

  it("el espejo del servidor RECHAZA una cotización que no cumple el contrato", () => {
    expect(
      cotizacionPaseClienteSchema.safeParse({
        ...COTIZACION.data,
        total: 70,
      }).success,
    ).toBe(false);

    expect(
      cotizacionPaseClienteSchema.safeParse({
        ...COTIZACION.data,
        version: "",
      }).success,
    ).toBe(false);
  });
});

describe("ACP — el cuerpo de la compra asistida de un pase", () => {
  it("el cuerpo NO lleva precio ni total: los calcula el servidor", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: CLIENTE,
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
      },
    });

    const cuerpo = apiSendMock.mock.calls.at(-1)?.[2] as Record<
      string,
      unknown
    >;
    const evidencia = cuerpo.evidencia as Record<string, unknown>;

    expect(Object.keys(cuerpo)).not.toContain("total");
    expect(Object.keys(cuerpo)).not.toContain("precio");
    expect(Object.keys(evidencia)).not.toContain("total");
    expect(Object.keys(evidencia)).not.toContain("precio");
    expect(Object.keys(evidencia)).not.toContain("moneda");
  });

  it("el importe declarado viaja SOLO cuando el administrador lo declara", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: CLIENTE,
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
        monto_declarado: "60.00",
      },
    });

    const evidencia = (
      apiSendMock.mock.calls.at(-1)?.[2] as {
        evidencia: Record<string, unknown>;
      }
    ).evidencia;

    expect(evidencia.monto_declarado).toBe("60.00");
  });

  it("un importe que NO se declaró NO viaja: su ausencia ya lo dice", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: CLIENTE,
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
      },
    });

    const evidencia = (
      apiSendMock.mock.calls.at(-1)?.[2] as {
        evidencia: Record<string, unknown>;
      }
    ).evidencia;

    expect(Object.keys(evidencia)).not.toContain("monto_declarado");
    expect(Object.keys(evidencia)).not.toContain("precio_version");
  });

  it("el token del precio cotizado viaja con el comando", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: CLIENTE,
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
        precio_version: "9f2c1a7b4d5e6f80",
      },
    });

    const evidencia = (
      apiSendMock.mock.calls.at(-1)?.[2] as {
        evidencia: Record<string, unknown>;
      }
    ).evidencia;

    expect(evidencia.precio_version).toBe("9f2c1a7b4d5e6f80");
  });

  it("el total que devuelve el servidor NO es el importe declarado", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    const resultado = await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: CLIENTE,
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
        monto_declarado: "60.00",
      },
    });

    // El importe declarado es EVIDENCIA; el total es el del servidor.
    expect(resultado.total).toBe("70.00");
    expect(resultado.monto_declarado).toBe("60.00");
  });

  it("el pedido de la tienda NO lleva importe declarado ni token de precio", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPedidoCliente({
      items: [{ tipo: "PRODUCTO", producto_id: "producto-1", cantidad: 3 }],
      cliente: CLIENTE,
      evidencia: {
        canal: "YAPE",
        referencia: "OP-9988",
        motivo: "Pago por Yape.",
      },
    });

    const evidencia = (
      apiSendMock.mock.calls.at(-1)?.[2] as {
        evidencia: Record<string, unknown>;
      }
    ).evidencia;

    expect(Object.keys(evidencia).sort()).toEqual([
      "canal",
      "motivo",
      "referencia",
    ]);
  });
});

describe("ACP — los espejos del importe declarado", () => {
  it("el importe declarado es un decimal de hasta DOS decimales", () => {
    const base = {
      canal: "EFECTIVO",
      referencia: "REC-0001",
      motivo: "Cobro en la boletería.",
    };

    for (const monto of ["0", "35", "35.5", "35.50", "0.00"]) {
      expect(
        evidenciaPagoCompraPaseSchema.safeParse({
          ...base,
          monto_declarado: monto,
        }).success,
      ).toBe(true);
    }

    for (const monto of ["35.555", "-5", "abc", "35.50.10", " 35,50"]) {
      expect(
        evidenciaPagoCompraPaseSchema.safeParse({
          ...base,
          monto_declarado: monto,
        }).success,
      ).toBe(false);
    }
  });

  it("el importe declarado es OPCIONAL: su ausencia significa «no declarado»", () => {
    const resultado = evidenciaPagoCompraPaseSchema.safeParse({
      canal: "EFECTIVO",
      referencia: "REC-0001",
      motivo: "Cobro en la boletería.",
    });

    expect(resultado.success).toBe(true);
    if (!resultado.success) return;
    expect(resultado.data.monto_declarado).toBeUndefined();
  });

  it("el formulario acepta un importe vacío y RECHAZA uno que no es un decimal", () => {
    const base = {
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      contacto_email: "rosa@example.com",
      cantidad: 2,
      canal: "EFECTIVO",
      referencia: "REC-0001",
      motivo: "Cobro en la boletería.",
    };

    expect(
      compraParaClienteFormSchema.safeParse({ ...base, monto_declarado: "" })
        .success,
    ).toBe(true);
    expect(
      compraParaClienteFormSchema.safeParse({
        ...base,
        monto_declarado: "60.00",
      }).success,
    ).toBe(true);
    expect(
      compraParaClienteFormSchema.safeParse({
        ...base,
        monto_declarado: "60.000",
      }).success,
    ).toBe(false);
  });
});

describe("ACP — los fallos de la compra asistida", () => {
  it("el 409 del precio movido se reconoce y SÓLO ése", () => {
    expect(
      esPrecioCambiado(
        new ErrorAdmin(409, "PRECIO_CAMBIADO", "El precio cambió."),
      ),
    ).toBe(true);

    expect(
      esPrecioCambiado(
        new ErrorAdmin(409, "PASE_NO_DISPONIBLE", "No está a la venta."),
      ),
    ).toBe(false);

    expect(
      esPrecioCambiado(
        new ErrorAdmin(422, "PRECIO_CAMBIADO", "El precio cambió."),
      ),
    ).toBe(false);

    expect(esPrecioCambiado(new Error("boom"))).toBe(false);
  });

  it("el error de cada campo llega al control que lo posee", () => {
    const error = new ErrorAdmin(422, "VALIDATION_ERROR", "Revisa los datos.", [
      {
        campo: "evidencia.referencia",
        codigo: "INVALID_VALUE",
        mensaje: "La referencia no es válida.",
      },
      {
        campo: "evidencia.monto_declarado",
        codigo: "INVALID_VALUE",
        mensaje: "El importe declarado no es válido.",
      },
    ]);

    expect(erroresDeCampoDeLaCompra(error)).toEqual({
      referencia: "La referencia no es válida.",
      monto_declarado: "El importe declarado no es válido.",
    });
  });

  it("un error de un campo que el formulario NO dibuja NO se inventa", () => {
    const error = new ErrorAdmin(422, "VALIDATION_ERROR", "Revisa los datos.", [
      {
        campo: "pase_id",
        codigo: "INVALID_VALUE",
        mensaje: "El pase no existe.",
      },
      {
        campo: "evidencia.precio_version",
        codigo: "INVALID_VALUE",
        mensaje: "La cotización venció.",
      },
    ]);

    expect(erroresDeCampoDeLaCompra(error)).toEqual({});
  });
});
