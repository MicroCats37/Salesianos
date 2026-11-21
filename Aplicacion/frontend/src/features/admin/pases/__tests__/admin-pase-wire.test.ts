import { describe, expect, it, vi } from "vitest";
import { parseFieldErrors } from "@/errors";
import {
  ErrorAdmin,
  ErrorContratoAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { apiSend } from "@/lib/api";
import {
  adminCortesiaListaItemSchema,
  adminCortesiaSchema,
  cortesiaPaseFormSchema,
  revocarCortesiaFormSchema,
} from "../schemas/admin.pase.schema";
import {
  emitirCredencial,
  listarCortesias,
  otorgarCortesia,
  revocarCortesia,
  rutaCortesias,
  rutaEmitirCredencial,
  rutaRevocarCortesia,
} from "../services/admin.pase.service";
import { adminPaseClaves } from "../utils/admin.pase.claves.utils";

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

const apiSendMock = vi.mocked(apiSend);

/** The answer of the grant of a courtesy. */
const CORTESIA = {
  success: true,
  data: {
    id: "cortesia-1",
    derecho_id: "derecho-1",
    edicion_id: "edicion-1",
    edicion_nombre: "EDICION DE EJEMPLO",
    pase_id: "pase-1",
    pase_nombre: "Pase FEST",
    persona_id: "persona-1",
    persona_nombres: "Rosa Díaz",
    persona_tipo_documento: "DNI",
    persona_numero_documento: "77777777",
    estado: "ACTIVA",
    motivo: "Cortesía de la organización.",
    actor_usuario_id: null,
    actor_nombres: "Administrador",
    concedido_en: "2026-11-20T10:00:00Z",
    revocado_en: null,
  },
  error: null,
  message: null,
};

/** The answer of the revocation of a courtesy. */
const REVOCADA = {
  success: true,
  data: {
    ...CORTESIA.data,
    estado: "REVOCADA",
    motivo_revocacion: "La persona ya no asiste al evento.",
    revocado_en: "2026-11-21T10:00:00Z",
    ya_revocado: false,
  },
  error: null,
  message: null,
};

/** The answer of the issue of the credential. */
const CREDENCIAL = {
  success: true,
  data: {
    ticket_id: "ticket-1",
    codigo: "FEST-secreto-de-ejemplo",
    tipo_derecho: "ENTRADA_CORTESIA",
    operacion: "INGRESO",
    edicion_id: "edicion-1",
    emitido_en: "2026-11-21T10:00:00Z",
  },
  error: null,
  message: null,
};

/** A page of the list of the courtesies. */
const LISTA = {
  success: true,
  data: {
    items: [
      {
        id: "cortesia-1",
        pase_nombre: "Pase FEST",
        edicion_nombre: "EDICION DE EJEMPLO",
        persona_nombres: "Rosa Díaz",
        persona_tipo_documento: "DNI",
        persona_numero_documento: "77777777",
        estado: "ACTIVA",
        motivo: "Cortesía de la organización.",
        actor_nombres: "Administrador",
        concedido_en: "2026-11-20T10:00:00Z",
        derecho_id: "derecho-1",
      },
    ],
    total: 1,
    page: 1,
    page_size: 25,
    total_pages: 1,
  },
  error: null,
  message: null,
};

/** The identity of a person that the padrón already knows. */
const IDENTIDAD = {
  tipo_documento: "DNI",
  numero_documento: "77777777",
  nombres: "Rosa",
  apellidos: "Díaz",
  genero: "",
  estado_identidad: "ENCONTRADA",
};

describe("ADP — las rutas de las cortesías son las del ledger", () => {
  it("las cuatro rutas son las congeladas", () => {
    expect(rutaCortesias()).toBe("/administracion/pases/cortesias");
    expect(rutaRevocarCortesia("cortesia-1")).toBe(
      "/administracion/pases/cortesias/cortesia-1/revocar",
    );
    expect(rutaEmitirCredencial()).toBe("/validaciones/tickets");
  });

  it("la lista viaja con sus filtros y la respuesta es una página", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: LISTA });

    const pagina = await listarCortesias({
      edicion_id: "edicion-1",
      estado: "ACTIVA",
      page: 2,
      page_size: 25,
    });

    expect(pagina.total).toBe(1);
    expect(pagina.items[0].persona_nombres).toBe("Rosa Díaz");

    const [metodo, url, cuerpo, config] = apiSendMock.mock.calls[0] as [
      string,
      string,
      undefined,
      { params: Record<string, unknown> },
    ];
    expect(metodo).toBe("get");
    expect(url).toBe("/administracion/pases/cortesias");
    expect(cuerpo).toBeUndefined();
    expect(config.params).toEqual({
      edicion_id: "edicion-1",
      estado: "ACTIVA",
      page: 2,
      page_size: 25,
    });
  });
});

describe("ADP — el otorgamiento de una cortesía", () => {
  it("el comando viaja con la identidad y el motivo, y SIN ningún importe", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: CORTESIA });

    const resultado = await otorgarCortesia({
      edicion_id: "edicion-1",
      pase_id: "pase-1",
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      motivo: "Cortesía de la organización.",
    });

    expect(resultado.estado).toBe("ACTIVA");
    expect(resultado.persona_id).toBe("persona-1");
    // El DERECHO viaja en la respuesta del otorgamiento: la credencial se
    // emite contra él sin otro viaje.
    expect(resultado.derecho_id).toBe("derecho-1");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      Record<string, unknown>,
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/pases/cortesias");
    expect(cuerpo).toEqual({
      edicion_id: "edicion-1",
      pase_id: "pase-1",
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      motivo: "Cortesía de la organización.",
    });

    // Una cortesía NO tiene hechos financieros: ningún importe viaja.
    expect(Object.keys(cuerpo)).not.toContain("total");
    expect(Object.keys(cuerpo)).not.toContain("precio");
    expect(Object.keys(cuerpo)).not.toContain("monto");
    expect(Object.keys(cuerpo)).not.toContain("moneda");
  });

  it("el actor NO viaja: lo pone el servidor", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: CORTESIA });

    await otorgarCortesia({
      edicion_id: "edicion-1",
      pase_id: "pase-1",
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      motivo: "Cortesía de la organización.",
    });

    const cuerpo = apiSendMock.mock.calls.at(-1)?.[2] as Record<
      string,
      unknown
    >;
    expect(Object.keys(cuerpo)).not.toContain("actor_usuario_id");
    expect(Object.keys(cuerpo)).not.toContain("actor_nombres");
  });
});

describe("ADP — la revocación de una cortesía", () => {
  it("el identificador viaja en la RUTA y el motivo en el cuerpo", async () => {
    apiSendMock.mockResolvedValue({ status: 200, data: REVOCADA });

    const resultado = await revocarCortesia("cortesia-1", {
      motivo: "La persona ya no asiste al evento.",
    });

    expect(resultado.ya_revocado).toBe(false);
    expect(resultado.estado).toBe("REVOCADA");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      Record<string, unknown>,
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/administracion/pases/cortesias/cortesia-1/revocar");
    expect(cuerpo).toEqual({ motivo: "La persona ya no asiste al evento." });
  });

  it("sin motivo no hay revocación: el cuerpo se valida antes de salir", async () => {
    await expect(
      revocarCortesia("cortesia-1", { motivo: "cort" }),
    ).rejects.toThrow();

    expect(apiSendMock).not.toHaveBeenCalled();
  });
});

describe("ADP — la credencial de la puerta", () => {
  it("el comando declara SOLO el derecho", async () => {
    apiSendMock.mockResolvedValue({ status: 201, data: CREDENCIAL });

    const credencial = await emitirCredencial({ derecho_id: "derecho-1" });

    expect(credencial.codigo).toBe("FEST-secreto-de-ejemplo");

    const [metodo, url, cuerpo] = apiSendMock.mock.calls[0] as [
      string,
      string,
      Record<string, unknown>,
    ];
    expect(metodo).toBe("post");
    expect(url).toBe("/validaciones/tickets");
    expect(cuerpo).toEqual({ derecho_id: "derecho-1" });

    // El tipo del derecho y la operación los DERIVA el servidor.
    expect(Object.keys(cuerpo)).not.toContain("tipo_derecho");
    expect(Object.keys(cuerpo)).not.toContain("operacion");
    expect(Object.keys(cuerpo)).not.toContain("codigo");
  });
});

describe("ADP — los fallos del backend", () => {
  it("un 409 llega con su estado y su código, sin perder la prosa pública", async () => {
    apiSendMock.mockRejectedValue({
      response: {
        status: 409,
        data: {
          success: false,
          data: null,
          error: {
            code: "PASE_DUPLICADO",
            message:
              "La persona ya tiene una entrada activa de este pase en esta edición.",
            details: null,
            field_errors: null,
          },
          message: null,
        },
      },
    });

    await expect(
      otorgarCortesia({
        edicion_id: "edicion-1",
        pase_id: "pase-1",
        tipo_documento: "DNI",
        numero_documento: "77777777",
        nombres: "Rosa",
        apellidos: "Díaz",
        motivo: "Cortesía de la organización.",
      }),
    ).rejects.toMatchObject({
      status: 409,
      codigo: "PASE_DUPLICADO",
      message:
        "La persona ya tiene una entrada activa de este pase en esta edición.",
    });
  });

  it("un 422 lleva sus errores de campo al control que corresponde", async () => {
    const envelope = {
      success: false,
      data: null,
      error: {
        code: "CORTESIA_MOTIVO_INVALIDO",
        message: "El motivo de la cortesía no es válido.",
        details: null,
        field_errors: [
          {
            field: "motivo",
            code: "CORTESIA_MOTIVO_INVALIDO",
            message: "El motivo necesita al menos 5 caracteres.",
          },
        ],
      },
      message: null,
    };

    apiSendMock.mockRejectedValue({
      response: { status: 422, data: envelope },
    });

    const fallo = await otorgarCortesia({
      edicion_id: "edicion-1",
      pase_id: "pase-1",
      tipo_documento: "DNI",
      numero_documento: "77777777",
      nombres: "Rosa",
      apellidos: "Díaz",
      motivo: "Cortesía de la organización.",
    }).catch((error: unknown) => error);

    expect(fallo).toBeInstanceOf(ErrorAdmin);
    const admin = fallo as ErrorAdmin;
    expect(admin.status).toBe(422);
    expect(admin.erroresDeCampo).toEqual([
      {
        campo: "motivo",
        codigo: "CORTESIA_MOTIVO_INVALIDO",
        mensaje: "El motivo necesita al menos 5 caracteres.",
      },
    ]);

    // El cuerpo crudo viaja con el error: el formulario es el dueño de los
    // errores de campo y los reparte con `setError`.
    const crudo = (admin as unknown as { response?: { data?: unknown } })
      .response?.data;
    expect(parseFieldErrors(crudo)).toEqual({
      motivo: "El motivo necesita al menos 5 caracteres.",
    });
  });

  it("una respuesta que no cumple el contrato es un fallo RUIDOSO", async () => {
    apiSendMock.mockResolvedValue({
      status: 201,
      data: { success: true, data: { id: "cortesia-1" }, error: null },
    });

    await expect(
      otorgarCortesia({
        edicion_id: "edicion-1",
        pase_id: "pase-1",
        tipo_documento: "DNI",
        numero_documento: "77777777",
        nombres: "Rosa",
        apellidos: "Díaz",
        motivo: "Cortesía de la organización.",
      }),
    ).rejects.toBeInstanceOf(ErrorContratoAdmin);
  });
});

describe("ADP — los espejos de la fila y del acta", () => {
  it("una fila SIN derecho publica el identificador como AUSENTE", () => {
    const fila = adminCortesiaListaItemSchema.safeParse({
      id: "cortesia-1",
      pase_nombre: "Pase FEST",
      edicion_nombre: "EDICION DE EJEMPLO",
      persona_nombres: "Rosa Díaz",
      persona_tipo_documento: "DNI",
      persona_numero_documento: "77777777",
      estado: "ACTIVA",
      motivo: "Cortesía de la organización.",
      actor_nombres: "Administrador",
      concedido_en: "2026-11-20T10:00:00Z",
      derecho_id: null,
    });

    expect(fila.success).toBe(true);
    if (!fila.success) return;
    expect(fila.data.derecho_id).toBeNull();
  });

  it("una fila SIN la CLAVE del identificador NO cumple el contrato", () => {
    // El backend SIEMPRE publica la clave: su ausencia es un contrato roto,
    // no una cortesía sin derecho. El espejo NO la vuelve opcional.
    const fila = adminCortesiaListaItemSchema.safeParse({
      id: "cortesia-1",
      pase_nombre: "Pase FEST",
      edicion_nombre: "EDICION DE EJEMPLO",
      persona_nombres: "Rosa Díaz",
      persona_tipo_documento: "DNI",
      persona_numero_documento: "77777777",
      estado: "ACTIVA",
      motivo: "Cortesía de la organización.",
      actor_nombres: "Administrador",
      concedido_en: "2026-11-20T10:00:00Z",
    });

    expect(fila.success).toBe(false);
  });

  it("una fila CON el identificador del DERECHO se lee sin perderlo", () => {
    const fila = adminCortesiaListaItemSchema.safeParse({
      id: "cortesia-1",
      pase_nombre: "Pase FEST",
      edicion_nombre: "EDICION DE EJEMPLO",
      persona_nombres: "Rosa Díaz",
      persona_tipo_documento: "DNI",
      persona_numero_documento: "77777777",
      estado: "ACTIVA",
      motivo: "Cortesía de la organización.",
      actor_nombres: "Administrador",
      concedido_en: "2026-11-20T10:00:00Z",
      derecho_id: "derecho-1",
    });

    expect(fila.success).toBe(true);
    if (!fila.success) return;
    expect(fila.data.derecho_id).toBe("derecho-1");
  });

  it("el acta de la cortesía publica el DERECHO que creó", () => {
    // El derecho nace CON el acta, en la misma transacción: su identificador
    // es OBLIGATORIO en la respuesta del otorgamiento.
    const acta = adminCortesiaSchema.safeParse({
      id: "cortesia-1",
      derecho_id: "derecho-1",
      edicion_id: "edicion-1",
      edicion_nombre: "EDICION DE EJEMPLO",
      pase_id: "pase-1",
      pase_nombre: "Pase FEST",
      persona_id: "persona-1",
      persona_nombres: "Rosa Díaz",
      persona_tipo_documento: "DNI",
      persona_numero_documento: "77777777",
      estado: "ACTIVA",
      motivo: "Cortesía de la organización.",
      actor_usuario_id: null,
      actor_nombres: "Administrador",
      concedido_en: "2026-11-20T10:00:00Z",
      revocado_en: null,
    });

    expect(acta.success).toBe(true);
    if (!acta.success) return;
    expect(acta.data.derecho_id).toBe("derecho-1");

    // Y un acta SIN el identificador NO cumple el contrato.
    const sinDerecho = adminCortesiaSchema.safeParse({
      ...{
        id: "cortesia-1",
        edicion_id: "edicion-1",
        edicion_nombre: "EDICION DE EJEMPLO",
        pase_id: "pase-1",
        pase_nombre: "Pase FEST",
        persona_id: "persona-1",
        persona_nombres: "Rosa Díaz",
        persona_tipo_documento: "DNI",
        persona_numero_documento: "77777777",
        estado: "ACTIVA",
        motivo: "Cortesía de la organización.",
        actor_usuario_id: null,
        actor_nombres: "Administrador",
        concedido_en: "2026-11-20T10:00:00Z",
        revocado_en: null,
      },
    });

    expect(sinDerecho.success).toBe(false);
  });
});

describe("ADP — el formulario de la cortesía", () => {
  it("exige el motivo, la identidad resuelta y la confirmación sin cobro", () => {
    const completo = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      pase_id: "pase-1",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: true,
    });

    expect(completo.success).toBe(true);

    const sinMotivo = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      pase_id: "pase-1",
      motivo: "cort",
      confirma_sin_cobro: true,
    });
    expect(sinMotivo.success).toBe(false);

    const sinPase = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      pase_id: "",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: true,
    });
    expect(sinPase.success).toBe(false);

    const sinConfirmacion = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      pase_id: "pase-1",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: false,
    });
    expect(sinConfirmacion.success).toBe(false);

    const sinConsultar = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      estado_identidad: "SIN_CONSULTAR",
      pase_id: "pase-1",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: true,
    });
    expect(sinConsultar.success).toBe(false);
  });

  it("una identidad que hay que registrar exige los nombres", () => {
    const sinNombres = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      estado_identidad: "NO_ENCONTRADA",
      nombres: "",
      apellidos: "",
      pase_id: "pase-1",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: true,
    });

    expect(sinNombres.success).toBe(false);
  });

  it("el género NO se exige: el contrato de la cortesía no lo transporta", () => {
    const sinGenero = cortesiaPaseFormSchema.safeParse({
      ...IDENTIDAD,
      estado_identidad: "NO_ENCONTRADA",
      nombres: "Rosa",
      apellidos: "Díaz",
      genero: "",
      pase_id: "pase-1",
      motivo: "Cortesía de la organización.",
      confirma_sin_cobro: true,
    });

    expect(sinGenero.success).toBe(true);
  });

  it("el formulario de la revocación exige un motivo de verdad", () => {
    expect(
      revocarCortesiaFormSchema.safeParse({ motivo: "La persona no asiste." })
        .success,
    ).toBe(true);
    expect(
      revocarCortesiaFormSchema.safeParse({ motivo: "cort" }).success,
    ).toBe(false);
    expect(revocarCortesiaFormSchema.safeParse({ motivo: "" }).success).toBe(
      false,
    );
  });
});

describe("ADP — el namespace de las claves es propio", () => {
  it("las cortesías viven en su propio namespace", () => {
    expect(adminPaseClaves.cortesias()).toEqual([
      "admin",
      "pases",
      "cortesias",
    ]);
    expect(adminPaseClaves.todas).toEqual(["admin", "pases"]);
  });

  it("la clave de UNA lectura lleva sus parámetros", () => {
    expect(
      adminPaseClaves.cortesiasParams({ edicion_id: "edicion-1", page: 2 }),
    ).toEqual([
      "admin",
      "pases",
      "cortesias",
      { edicion_id: "edicion-1", page: 2 },
    ]);

    // Un parámetro ausente NO crea una segunda entrada de caché.
    expect(adminPaseClaves.cortesiasParams({ page: undefined })).toEqual([
      "admin",
      "pases",
      "cortesias",
    ]);
  });
});
