import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { QueryClient } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiSend } from "@/lib/api";
import {
  ErrorAdmin,
  ErrorRutaAdminNoRegistrada,
  pedirAdmin,
  RUTAS_ADMIN,
  urlDeRutaAdmin,
} from "../services/admin.service";
import { invalidarAdmin } from "../utils/admin.cache.utils";
import { adminClaves } from "../utils/admin.claves.utils";
import {
  estadoDesdeConsulta,
  erroresDeCampoDeError,
  mensajeDeError,
  statusDeError,
} from "../utils/admin.estado.utils";
import {
  parametrosConsultaAdmin,
  parametrosListaAdminDesdeUrl,
} from "../utils/admin.filtros.utils";
import {
  payloadAprobarPagoManualAdmin,
  payloadRetirarParticipanteAdmin,
} from "../utils/admin.payload.utils";

vi.mock("@/lib/api", () => ({
  apiSend: vi.fn(),
}));

const apiSendMock = vi.mocked(apiSend);

/** An envelope that the mirrors of the area accept. */
const ENVOLOPE = {
  success: true,
  data: { items: [], total: 0, page: 1, page_size: 25, total_pages: 0 },
  error: null,
  message: null,
};

const ESPEJO = {
  safeParse: (valor: unknown) => ({
    success: true,
    data: { success: true, data: ENVOLOPE.data },
  }),
} as never;

beforeEach(() => {
  apiSendMock.mockReset();
});

describe("API-04 — el ledger de las rutas administrativas", () => {
  it("cada ruta declara su verdad de registro y su motivo", () => {
    for (const [id, ruta] of Object.entries(RUTAS_ADMIN)) {
      expect(ruta.ledger, `la ruta ${id} declara su id del ledger`).toBeTruthy();
      expect(ruta.presentador, `la ruta ${id} declara su presentador`).toBeTruthy();
      expect(ruta.wrapper, `la ruta ${id} declara su wrapper`).toBeTruthy();
      expect(ruta.motivo, `la ruta ${id} declara el motivo`).toBeTruthy();
      expect(ruta.permiso, `la ruta ${id} declara el permiso`).toBeTruthy();
    }
  });

  it("NINGUNA ruta administrativa está registrada en el backend (2026-11-19)", () => {
    // La verdad de `Aplicacion/backend/config/api.py`: ni
    // `AdminInscripcionController`, ni `AdminEquipoController`, ni
    // `AdminParticipanteController`, ni `AdminPagoController`, ni
    // `AdminPersonaController` están registrados.
    const registradas = Object.entries(RUTAS_ADMIN).filter(
      ([, ruta]) => ruta.registrado,
    );

    expect(registradas.map(([id]) => id)).toEqual([]);
  });
});

describe("API-04 — una ruta que no existe NO se llama", () => {
  it("el guard rechaza la ruta antes del transporte", () => {
    expect(() => urlDeRutaAdmin(RUTAS_ADMIN.inscripcionesLista)).toThrow(
      ErrorRutaAdminNoRegistrada,
    );

    expect(apiSendMock).not.toHaveBeenCalled();
  });

  it("una orden forzada de una ruta inexistente falla SIN issuing una petición", async () => {
    await expect(
      pedirAdmin(RUTAS_ADMIN.aprobarPagoManual, ESPEJO, {
        pathParams: { orden_pago_id: "orden-1" },
        payload: { motivo: "MOTIVO" },
      }),
    ).rejects.toBeInstanceOf(ErrorRutaAdminNoRegistrada);

    expect(apiSendMock).not.toHaveBeenCalled();
  });

  it("la retirada de un participante tampoco sale: no hay ruta administrativa", async () => {
    await expect(
      pedirAdmin(RUTAS_ADMIN.retirarParticipante, ESPEJO, {
        pathParams: {
          inscripcion_id: "inscripcion-1",
          participacion_id: "participacion-1",
        },
        payload: { motivo: "MOTIVO" },
      }),
    ).rejects.toBeInstanceOf(ErrorRutaAdminNoRegistrada);

    expect(apiSendMock).not.toHaveBeenCalled();
  });

  it("el mensaje del guard nombra el ledger y el motivo", () => {
    let mensaje = "";

    try {
      urlDeRutaAdmin(RUTAS_ADMIN.pagosLista);
    } catch (error) {
      mensaje = (error as Error).message;
    }

    expect(mensaje).toContain("RT-PG-04");
    expect(mensaje).toContain("AdminPagoController");
  });
});

describe("API-04 — el mapeo de los filtros de la URL", () => {
  it("sólo viajan los parámetros declarados", () => {
    const parametros = parametrosListaAdminDesdeUrl({
      q: "PERSONA",
      estado_operativo: "PENDIENTE",
      inventado: "NO",
    });

    expect(parametros.q).toBe("PERSONA");
    expect(parametros.estado_operativo).toBe("PENDIENTE");
    expect(Object.keys(parametros)).not.toContain("inventado");
  });

  it("la página y el tamaño se parsean como enteros positivos", () => {
    const parametros = parametrosListaAdminDesdeUrl({
      page: "3",
      page_size: "50",
    });

    expect(parametros.page).toBe(3);
    expect(parametros.page_size).toBe(50);
  });

  it("una página que no es un entero positivo se descarta", () => {
    const parametros = parametrosListaAdminDesdeUrl({
      page: "0",
      page_size: "muchos",
    });

    expect(parametros.page).toBeUndefined();
    expect(parametros.page_size).toBeUndefined();
  });

  it("un parámetro ausente NO viaja en la petición", () => {
    const consulta = parametrosConsultaAdmin({ page: 1, q: undefined });

    expect(consulta).toEqual({ page: 1 });
    expect(Object.keys(consulta)).not.toContain("q");
  });
});

describe("API-04 — las claves de la caché", () => {
  it("cada dataset tiene su propio namespace", () => {
    expect(adminClaves.inscripciones.all).toEqual(["admin.inscripciones"]);
    expect(adminClaves.equipos.all).toEqual(["admin.equipos"]);
    expect(adminClaves.participantes.all).toEqual(["admin.participantes"]);
    expect(adminClaves.pagos.all).toEqual(["admin.pagos"]);
  });

  it("la edición, el filtro, la página y el registro viajan en la clave", () => {
    const clave = adminClaves.pagos.listPage({
      edicion_id: "edicion-1",
      estado_operativo: "PENDIENTE",
      page: 2,
    });

    expect(clave).toEqual([
      "admin.pagos",
      "list",
      { edicion_id: "edicion-1", estado_operativo: "PENDIENTE", page: 2 },
    ]);
  });

  it("un parámetro ausente NO crea una segunda entrada", () => {
    const conAusente = adminClaves.pagos.listPage({
      page: 1,
      q: undefined,
    });
    const sinParametro = adminClaves.pagos.listPage({ page: 1 });

    expect(conAusente).toEqual(sinParametro);
  });

  it("el registro y la versión viajan en la clave de la acción", () => {
    expect(
      adminClaves.accion("pagos", "compra-1", "v3"),
    ).toEqual([
      "admin",
      "pagos",
      "accion",
      { registro_id: "compra-1", version: "v3" },
    ]);
  });
});

describe("API-04 — el estado de una superficie", () => {
  it("una ruta que no existe muestra el estado honesto", () => {
    const estado = estadoDesdeConsulta(
      { isPending: true, isError: false, data: undefined, error: null },
      false,
    );

    expect(estado).toEqual({ estado: "sin-datos" });
  });

  it("una lectura en vuelo NO se dibuja como una lista vacía", () => {
    const estado = estadoDesdeConsulta(
      { isPending: true, isError: false, data: undefined, error: null },
      true,
    );

    expect(estado).toEqual({ estado: "cargando" });
  });

  it("un 403 es un estado de PERMISO, con la prosa del backend", () => {
    const error = new ErrorAdmin(403, "ACTION_NOT_ALLOWED", "No tienes permiso.");

    const estado = estadoDesdeConsulta(
      { isPending: false, isError: true, data: undefined, error },
      true,
    );

    expect(estado).toEqual({
      estado: "sin-permiso",
      mensaje: "No tienes permiso.",
    });
  });

  it("un 409 y un 500 son fallos RECUPERABLES con el mensaje del servidor", () => {
    const conflicto = estadoDesdeConsulta(
      {
        isPending: false,
        isError: true,
        data: undefined,
        error: new ErrorAdmin(409, "ORDEN_YA_PAGADA_CON_IZIPAY", "Ya está paga."),
      },
      true,
    );
    const caida = estadoDesdeConsulta(
      {
        isPending: false,
        isError: true,
        data: undefined,
        error: new ErrorAdmin(500, "ERROR_INTERNO", "Algo falló."),
      },
      true,
    );

    expect(conflicto).toEqual({ estado: "error", mensaje: "Ya está paga." });
    expect(caida).toEqual({ estado: "error", mensaje: "Algo falló." });
  });

  it("el estado de una lista toma los ÍTEMS de la página", () => {
    const estado = estadoDesdeConsulta(
      {
        isPending: false,
        isError: false,
        data: { items: [1, 2], total: 2, page: 1, page_size: 25, total_pages: 1 },
        error: null,
      },
      true,
      (pagina) => pagina.items,
    );

    expect(estado).toEqual({ estado: "listo", datos: [1, 2] });
  });
});

describe("API-04 — los errores de campo del 422", () => {
  it("el 422 lleva el error de campo a su control", () => {
    const error = new ErrorAdmin(422, "VALIDATION_ERROR", "Datos inválidos.", [
      { campo: "motivo", codigo: "REQUIRED", mensaje: "El motivo es obligatorio." },
    ]);

    expect(erroresDeCampoDeError(error)).toEqual({
      motivo: "El motivo es obligatorio.",
    });
  });

  it("un fallo que no es del backend no inventa errores de campo", () => {
    expect(erroresDeCampoDeError(new Error("boom"))).toEqual({});
  });

  it("el estado HTTP se lee del error y el mensaje es el del servidor", () => {
    const error = new ErrorAdmin(403, "ACTION_NOT_ALLOWED", "No tienes permiso.");

    expect(statusDeError(error)).toBe(403);
    expect(mensajeDeError(error)).toBe("No tienes permiso.");
  });
});

describe("API-04 — el refresco de la caché", () => {
  it("una operación de la lista invalida EXACTAMENTE su dataset", async () => {
    const cliente = new QueryClient();
    const invalida = vi.spyOn(cliente, "invalidateQueries");

    await invalidarAdmin(cliente, "pagos");

    expect(invalida).toHaveBeenCalledTimes(1);
    expect(invalida).toHaveBeenCalledWith({
      queryKey: ["admin.pagos"],
    });
  });

  it("una operación de la inscripción NO invalida los pagos", async () => {
    const cliente = new QueryClient();
    const invalida = vi.spyOn(cliente, "invalidateQueries");

    await invalidarAdmin(cliente, "inscripciones");

    expect(invalida).toHaveBeenCalledWith({
      queryKey: ["admin.inscripciones"],
    });
  });
});

describe("API-04 — los comandos sensibles llevan el motivo y la versión", () => {
  it("la retirada exige el motivo y no añade campos inventados", () => {
    const payload = payloadRetirarParticipanteAdmin({
      inscripcion_id: "inscripcion-1",
      participacion_id: "participacion-1",
      motivo: "  Motivo audited  ",
    });

    expect(payload).toEqual({
      inscripcion_id: "inscripcion-1",
      participacion_id: "participacion-1",
      motivo: "Motivo audited",
    });
    expect(Object.keys(payload)).not.toContain("version");
  });

  it("la aprobación manual envía el importe QUE PUBLICÓ el servidor", () => {
    const payload = payloadAprobarPagoManualAdmin({
      orden_pago_id: "orden-1",
      monto: "0.00",
      moneda: "PEN",
      motivo: "Pago recibido en efectivo",
      version: "v2",
    });

    expect(payload.monto).toBe("0.00");
    expect(payload.moneda).toBe("PEN");
    expect(payload.version).toBe("v2");
  });
});

describe("API-04 — NO queda ninguna fixture provisional", () => {
  const RAIZ = join(process.cwd(), "src", "features", "admin");

  /**
   * The marker of a provisional contract, matched WITHOUT writing it
   * literally: the search that closes the packet must find ZERO hits in this
   * area, and this file is part of the area.
   */
  const MARCADOR_PROVISIONAL = /PROVISIONAL_[A-Z_]*FIXTURE/;

  function ficheros(directorio: string): string[] {
    return readdirSync(directorio).flatMap((entrada) => {
      const ruta = join(directorio, entrada);

      if (statSync(ruta).isDirectory()) return ficheros(ruta);

      return ruta.endsWith(".ts") || ruta.endsWith(".tsx") ? [ruta] : [];
    });
  }

  it("ningún fichero de la zona lleva el marcador de fixture provisional", () => {
    const marcados = ficheros(RAIZ).filter((ruta) =>
      MARCADOR_PROVISIONAL.test(readFileSync(ruta, "utf8")),
    );

    expect(marcados).toEqual([]);
  });

  it("ningún fichero de la zona importa de una carpeta de fixtures", () => {
    const importadores = ficheros(RAIZ).filter((ruta) =>
      /from\s+"[^"]*fixtures\//.test(readFileSync(ruta, "utf8")),
    );

    expect(importadores).toEqual([]);
  });

  it("la carpeta de fixtures de la zona ya no existe", () => {
    expect(() => readdirSync(join(RAIZ, "fixtures"))).toThrow();
  });
});
