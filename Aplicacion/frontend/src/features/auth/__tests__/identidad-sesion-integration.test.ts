import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiSend } from "@/lib/api";
import {
  DocumentoConsultaSchema,
  PersonaConfirmarInSchema,
  PersonaResueltaSchema,
  PersonaSchema,
} from "../schemas/identidad.schema";
import { SesionUsuarioSchema } from "../schemas/sesion.schema";
import {
  confirmarPersona,
  consultarDocumento,
  PERSONA_BUSQUEDA_PATH,
  PERSONA_CONFIRMAR_PATH,
  PERSONA_RESOLVER_PATH,
  resolverPersona,
} from "../services/identidad.service";
import {
  obtenerSesionActual,
  SESION_ACTUAL_PATH,
} from "../services/sesion.service";
import { authClaves } from "../utils/auth.claves.utils";

/**
 * The integration of the identity and the session datasets.
 *
 * `RT-ID-01`…`RT-ID-03` (`/personas/**`) and `GET /auth/me` are the only
 * identity and session routes that are REGISTERED in
 * `Aplicacion/backend/config/api.py`. The suite freezes:
 *
 * 1. The Zod mirrors are EXACT: they accept the wrapper of the presenter and
 *    they reject an answer that does not match it.
 * 2. The routes are the registered ones.
 * 3. The keys live in one namespace and carry the identity of the dataset.
 */

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
  default: { get: vi.fn(), post: vi.fn() },
}));

const DOCUMENTO = {
  tipo_documento: "DNI",
  numero_documento: "12345678",
  nombre_completo: "PEREZ, ANA",
};

const PERSONA_RESUELTA = {
  tipo_documento: "DNI",
  numero_documento: "12345678",
  nombres: "ANA",
  apellidos: "PEREZ",
  origen: "EXTERNO",
  persona_id: null,
  persistida: false,
};

const PERSONA = {
  tipo_documento: "DNI",
  numero_documento: "12345678",
  nombres: "ANA",
  apellidos: "PEREZ",
  genero: "F",
  id: "33333333-3333-4333-8333-333333333333",
  origen_datos: "EXTERNO",
  datos_obtenidos_en: "2026-11-19T00:00:00Z",
  creado_en: "2026-11-19T00:00:00Z",
  actualizado_en: "2026-11-19T00:00:00Z",
};

const SESION = {
  id: "44444444-4444-4444-8444-444444444444",
  persona_id: "33333333-3333-4333-8333-333333333333",
  username: "ana",
  email: "ana@example.com",
  nombres: "ANA",
  apellidos: "PEREZ",
  rol: "normal",
  grupos: ["Normal"],
  es_admin: false,
  is_staff: false,
  is_superuser: false,
  nivel: "usuario",
  capacidades: [],
};

function envelope(data: unknown) {
  return { success: true, data, error: null, message: null };
}

beforeEach(() => {
  vi.mocked(apiSend).mockReset();
});

describe("el espejo de la identidad", () => {
  it("acepta el wrapper exacto de la consulta del documento", () => {
    expect(DocumentoConsultaSchema.parse(DOCUMENTO).nombre_completo).toBe(
      "PEREZ, ANA",
    );
  });

  it("acepta el wrapper exacto de la resolución", () => {
    const resuelta = PersonaResueltaSchema.parse(PERSONA_RESUELTA);

    expect(resuelta.persona_id).toBeNull();
    expect(resuelta.persistida).toBe(false);
  });

  it("acepta el wrapper exacto de la persona persistida", () => {
    expect(PersonaSchema.parse(PERSONA).origen_datos).toBe("EXTERNO");
  });

  it("rechaza una identidad a la que le falta un campo declarado", () => {
    const { origen_datos: _origen, ...incompleta } = PERSONA;

    expect(PersonaSchema.safeParse(incompleta).success).toBe(false);
  });

  it("la entrada de la confirmación declara sus campos y sus límites", () => {
    expect(
      PersonaConfirmarInSchema.safeParse({
        tipo_documento: "DNI",
        numero_documento: "12345678",
        nombres: "ANA",
        apellidos: null,
        genero: null,
      }).success,
    ).toBe(true);

    expect(
      PersonaConfirmarInSchema.safeParse({
        tipo_documento: "DNI",
        numero_documento: "12345678",
        nombres: "ANA",
        apellidos: null,
        genero: "X",
      }).success,
    ).toBe(false);
  });
});

describe("las rutas de la identidad", () => {
  it("consulta el documento en la ruta registrada", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope(DOCUMENTO),
    });

    const documento = await consultarDocumento("12345678");

    expect(apiSend).toHaveBeenCalledWith(
      "GET",
      `${PERSONA_BUSQUEDA_PATH}/12345678`,
    );
    expect(documento.numero_documento).toBe("12345678");
  });

  it("resuelve la identidad en la ruta registrada", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope(PERSONA_RESUELTA),
    });

    await resolverPersona({
      tipo_documento: "DNI",
      numero_documento: "12345678",
    });

    expect(apiSend).toHaveBeenCalledWith("POST", PERSONA_RESOLVER_PATH, {
      tipo_documento: "DNI",
      numero_documento: "12345678",
    });
  });

  it("confirma la identidad en la ruta registrada", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope(PERSONA),
    });

    await confirmarPersona({
      tipo_documento: "DNI",
      numero_documento: "12345678",
      nombres: "ANA",
      apellidos: "PEREZ",
      genero: "F",
    });

    expect(apiSend).toHaveBeenCalledWith("POST", PERSONA_CONFIRMAR_PATH, {
      tipo_documento: "DNI",
      numero_documento: "12345678",
      nombres: "ANA",
      apellidos: "PEREZ",
      genero: "F",
    });
  });
});

describe("el espejo y la ruta de la sesión", () => {
  it("acepta el wrapper exacto de la sesión", () => {
    const sesion = SesionUsuarioSchema.parse(SESION);

    expect(sesion.rol).toBe("normal");
    expect(sesion.grupos).toEqual(["Normal"]);
    expect(sesion.capacidades).toEqual([]);
  });

  it("rechaza una sesión a la que le falta un hecho declarado", () => {
    const { nivel: _nivel, ...incompleta } = SESION;

    expect(SesionUsuarioSchema.safeParse(incompleta).success).toBe(false);
  });

  it("lee la sesión en la ruta registrada", async () => {
    vi.mocked(apiSend).mockResolvedValue({
      status: 200,
      data: envelope(SESION),
    });

    const sesion = await obtenerSesionActual();

    expect(apiSend).toHaveBeenCalledWith("GET", SESION_ACTUAL_PATH);
    expect(sesion.username).toBe("ana");
  });
});

describe("la clave de la sesión y de la identidad", () => {
  it("vive en un solo namespace", () => {
    expect(authClaves.todas).toEqual(["auth"]);
    expect(authClaves.sesion()).toEqual(["auth", "sesion"]);
    expect(authClaves.identidad()).toEqual(["auth", "identidad"]);
  });

  it("la clave de un documento lleva su identidad", () => {
    expect(authClaves.documento("12345678")).toEqual([
      "auth",
      "identidad",
      "documento",
      "12345678",
    ]);
  });
});
