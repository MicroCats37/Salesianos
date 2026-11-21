import { describe, expect, it, vi } from "vitest";
import {
  RUTAS_ADMIN,
  urlDeRutaAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { apiSend } from "@/lib/api";
import {
  agregarParticipanteFormSchema,
  compraParaClienteFormSchema,
} from "../schemas/asistido.schema";
import {
  agregarParticipanteEquipo,
  comprarPaseCliente,
  comprarPedidoCliente,
} from "../services/asistido.service";

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

const apiSendMock = vi.mocked(apiSend);

/** An envelope that the mirrors of the area accept. */
const PARTICIPANTE = {
  success: true,
  data: {
    participacion_id: "participacion-1",
    persona_id: "persona-1",
    nombre: "María Quispe",
    documento: "33333333",
    equipo_id: "equipo-1",
    inscripcion_id: "inscripcion-1",
    rol: "JUGADOR",
    estado: "ACTIVA",
  },
  error: null,
  message: null,
};

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
    estado_pago: "PAGADA",
    comprador_persona_id: "persona-cliente",
    comprador_nombre: "Rosa Díaz",
    cantidad: 2,
  },
  error: null,
  message: null,
};

describe("ACP — el ledger de los comandos asistidos", () => {
  it("las tres rutas están registradas y declaran su verdad", () => {
    const rutas = [
      RUTAS_ADMIN.agregarParticipanteEquipo,
      RUTAS_ADMIN.comprarPaseCliente,
      RUTAS_ADMIN.comprarPedidoCliente,
    ];

    for (const ruta of rutas) {
      expect(ruta.registrado).toBe(true);
      expect(ruta.ledger).toBeTruthy();
      expect(ruta.presentador).toBeTruthy();
      expect(ruta.wrapper).toBeTruthy();
      expect(ruta.motivo).toBeTruthy();
      expect(ruta.permiso).toBeTruthy();
    }
  });

  it("el identificador del equipo viaja en la RUTA y no en el cuerpo", () => {
    const url = urlDeRutaAdmin(RUTAS_ADMIN.agregarParticipanteEquipo, {
      equipo_id: "equipo-1",
    });

    expect(url).toBe("/administracion/equipos/equipo-1/participantes");
  });
});

describe("ACP — el alta de un participante", () => {
  it("el comando viaja con el documento EXACTO, la identidad y el motivo auditado", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: PARTICIPANTE });

    const resultado = await agregarParticipanteEquipo("equipo-1", {
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "María",
      apellidos: "Quispe",
      genero: "F",
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    });

    expect(resultado.persona_id).toBe("persona-1");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      {
        nombres: string;
        apellidos: string;
        genero: string;
        rol: string;
      },
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/equipos/equipo-1/participantes");
    expect(cuerpo).toEqual({
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "María",
      apellidos: "Quispe",
      genero: "F",
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    });
  });

  it("una persona existente envía género nulo y deja que el padrón decida", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: PARTICIPANTE });

    await agregarParticipanteEquipo("equipo-1", {
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "María",
      apellidos: "Quispe",
      genero: "",
      rol: "JUGADOR",
      motivo: "Alta administrativa de participante en el equipo.",
    });

    const cuerpo = apiSendMock.mock.calls.at(-1)?.[2] as {
      genero: string | null;
    };
    expect(cuerpo.genero).toBeNull();
  });

  it("el formulario EXIGE el motivo y el documento", () => {
    const sinMotivo = agregarParticipanteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "María",
      apellidos: "Quispe",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      rol: "JUGADOR",
      motivo: "",
    });

    expect(sinMotivo.success).toBe(false);

    const sinDocumento = agregarParticipanteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "",
      nombres: "María",
      apellidos: "Quispe",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    });

    expect(sinDocumento.success).toBe(false);
  });

  it("valida el formato del documento con las mismas reglas del registro", () => {
    const identidadManual = {
      nombres: "Elena",
      apellidos: "Vega",
      genero: "F",
      estado_identidad: "NO_ENCONTRADA" as const,
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    };

    expect(
      agregarParticipanteFormSchema.safeParse({
        ...identidadManual,
        tipo_documento: "DNI",
        numero_documento: "1234567",
      }).success,
    ).toBe(false);
    expect(
      agregarParticipanteFormSchema.safeParse({
        ...identidadManual,
        tipo_documento: "CE",
        numero_documento: "12345678",
      }).success,
    ).toBe(false);
    expect(
      agregarParticipanteFormSchema.safeParse({
        ...identidadManual,
        tipo_documento: "PAS",
        numero_documento: "A12",
      }).success,
    ).toBe(false);
    expect(
      agregarParticipanteFormSchema.safeParse({
        ...identidadManual,
        tipo_documento: "CE",
        numero_documento: "123456789",
      }).success,
    ).toBe(true);
    expect(
      agregarParticipanteFormSchema.safeParse({
        ...identidadManual,
        tipo_documento: "PAS",
        numero_documento: "AB12",
      }).success,
    ).toBe(true);
  });

  it("el formulario EXIGE que la identidad se haya RESUELTO", () => {
    const sinConsultar = agregarParticipanteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "",
      apellidos: "",
      genero: "",
      estado_identidad: "SIN_CONSULTAR",
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    });

    expect(sinConsultar.success).toBe(false);
  });

  it("una identidad ENCONTRADA NO exige los nombres: el padrón manda", () => {
    const encontrada = agregarParticipanteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "33333333",
      nombres: "María",
      apellidos: "Quispe",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    });

    expect(encontrada.success).toBe(true);
  });

  it("una identidad NO ENCONTRADA EXIGE los nombres, los apellidos y el género", () => {
    const base = {
      tipo_documento: "DNI",
      numero_documento: "55555555",
      nombres: "",
      apellidos: "",
      genero: "",
      estado_identidad: "NO_ENCONTRADA" as const,
      rol: "JUGADOR",
      motivo: "Inscripción presencial.",
    };

    expect(agregarParticipanteFormSchema.safeParse(base).success).toBe(false);

    const sinGenero = agregarParticipanteFormSchema.safeParse({
      ...base,
      nombres: "Elena",
      apellidos: "Vega",
    });
    expect(sinGenero.success).toBe(false);

    const completa = agregarParticipanteFormSchema.safeParse({
      ...base,
      nombres: "Elena",
      apellidos: "Vega",
      genero: "F",
    });
    expect(completa.success).toBe(true);
  });
});

describe("ACP — la compra asistida", () => {
  it("el comprador es el CLIENTE declarado y el total NO viaja", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    const resultado = await comprarPaseCliente({
      pase_id: "pase-1",
      cantidad: 2,
      cliente: {
        tipo_documento: "DNI",
        numero_documento: "77777777",
        nombres: "Rosa",
        apellidos: "Díaz",
        genero: "F",
        contacto_email: "rosa@example.com",
      },
      evidencia: {
        canal: "EFECTIVO",
        referencia: "REC-0001",
        motivo: "Cobro en la boletería.",
      },
    });

    expect(resultado.comprador_persona_id).toBe("persona-cliente");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      {
        cliente: { numero_documento: string; genero: string };
        evidencia: { referencia: string };
      },
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/pases/compras-cliente");
    expect(cuerpo.cliente.numero_documento).toBe("77777777");
    expect(cuerpo.cliente.genero).toBe("F");
    expect(cuerpo.evidencia.referencia).toBe("REC-0001");
    expect(Object.keys(cuerpo)).not.toContain("total");
    expect(Object.keys(cuerpo)).not.toContain("precio");
  });

  it("el pedido de la tienda viaja con sus artículos y su evidencia", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: COMPRA });

    await comprarPedidoCliente({
      items: [{ tipo: "PRODUCTO", producto_id: "producto-1", cantidad: 3 }],
      cliente: {
        tipo_documento: "DNI",
        numero_documento: "77777777",
        nombres: "Rosa",
        apellidos: "Díaz",
        genero: "F",
        contacto_email: "rosa@example.com",
      },
      evidencia: {
        canal: "YAPE",
        referencia: "OP-9988",
        motivo: "Pago por Yape.",
      },
    });

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      {
        items: Array<{ tipo: string; producto_id: string; cantidad: number }>;
        cliente: { genero: string };
        evidencia: { canal: string };
      },
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/marketplace/pedidos-cliente");
    expect(cuerpo.items).toEqual([
      { tipo: "PRODUCTO", producto_id: "producto-1", cantidad: 3 },
    ]);
    expect(cuerpo.cliente.genero).toBe("F");
    expect(cuerpo.evidencia.canal).toBe("YAPE");
  });

  it("el formulario exige la identidad del cliente y la evidencia del pago", () => {
    const completo = compraParaClienteFormSchema.safeParse({
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
    });

    expect(completo.success).toBe(true);

    const sinEvidencia = compraParaClienteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      contacto_email: "rosa@example.com",
      cantidad: 2,
      canal: "EFECTIVO",
      referencia: "",
      motivo: "Cobro en la boletería.",
    });

    expect(sinEvidencia.success).toBe(false);

    const correoInvalido = compraParaClienteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      contacto_email: "no-es-un-correo",
      cantidad: 2,
      canal: "EFECTIVO",
      referencia: "REC-0001",
      motivo: "Cobro en la boletería.",
    });

    expect(correoInvalido.success).toBe(false);
  });

  it("la cantidad es SIEMPRE un entero positivo", () => {
    const cero = compraParaClienteFormSchema.safeParse({
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      genero: "F",
      estado_identidad: "ENCONTRADA",
      contacto_email: "",
      cantidad: 0,
      canal: "EFECTIVO",
      referencia: "REC-0001",
      motivo: "Cobro en la boletería.",
    });

    expect(cero.success).toBe(false);
  });

  it("el correo de contacto es EXCLUSIVO de la compra: la Persona no lo lleva", () => {
    const cuerpo = compraParaClienteFormSchema.safeParse({
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
    });

    expect(cuerpo.success).toBe(true);
    if (!cuerpo.success) return;

    // El correo viaja en el `cliente`, no en la identidad.
    expect(cuerpo.data.contacto_email).toBe("rosa@example.com");
    expect(Object.keys(cuerpo.data)).not.toContain("email");
  });
});
