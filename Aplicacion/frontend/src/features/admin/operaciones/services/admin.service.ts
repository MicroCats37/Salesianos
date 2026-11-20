import type { Method } from "axios";
import type { ZodType } from "zod";
import { getErrorMessage } from "@/errors";
import { apiSend } from "@/lib/api";
import { adminErrorEnvelopeSchema } from "../schemas/operaciones.schema";

/**
 * The ONE client of the administration area.
 *
 * ## The rule that decides everything here
 *
 * **A route does not exist until its controller is registered** in
 * `Aplicacion/backend/config/api.py` (`FR-07` §3.1 regla 2). A controller that
 * is written and not registered is DEAD CODE BY DESIGN: binding its route
 * would be binding an URL that answers 404.
 *
 * `RUTAS_ADMIN` is the ledger of this area with the VERIFICATION of that
 * rule, re-checked on 2026-11-20 against the live registration file:
 *
 * | Controller | Registered | Consequence |
 * |---|---|---|
 * | `AdminInscripcionController` | **NO** | `RT-IN-07`, `RT-IN-08` do not exist |
 * | `AdminEquipoController` | **NO** | `RT-IN-09`, `RT-IN-10` do not exist |
 * | `AdminParticipanteController` | **NO** | `RT-IN-11` does not exist |
 * | `AdminPagoController` | **NO** | `RT-PG-04`, `RT-PG-07` do not exist |
 * | `AdminPersonaController` | **NO** | `RT-ID-07`, `RT-ID-08` do not exist |
 * | `AdminController` | **NO** | `RT-ADM-01`, `RT-ADM-02` do not exist |
 *
 * The controllers of the first five rows EXIST in the target
 * (`Aplicacion/backend/modules/administracion/**`, work unit 2 of `XCT-02`)
 * and their code is COMPLETE: what is missing is the REGISTRATION, which is
 * A0's (`A0-XCT02-01`). Writing the controller is not binding the route.
 *
 * `RT-PG-05` (`POST /administracion/pagos/{orden_pago_id}/aprobar-manual`)
 * does NOT exist AND has no implementation: the target has no persisted
 * manual approval and the administration module must not own the commercial
 * settlement (`A0-XCT02-10`).
 *
 * `AdminPaseController` IS registered (`RT-PS-06`…`RT-PS-08`) but its routes
 * belong to the passes area and NOT to this packet: they are not bound here
 * (A0-API04-02).
 *
 * ## The guard
 *
 * `pedirAdmin()` builds the URL BEFORE it touches the transport and it
 * REJECTS a route that is not registered. A service function of this area can
 * therefore never issue a request to an URL that does not exist: the failure
 * is loud, local and immediate (`ErrorRutaAdminNoRegistrada`).
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 */

/** A route of the administration area, with its registration truth. */
export interface RutaAdmin {
  /** The id of the route in the ledger (`SH-05` §1.3). */
  readonly ledger: string;
  /** The HTTP method. */
  readonly metodo: Method;
  /** The path of the route, with its parameters as `{nombre}`. */
  readonly ruta: string;
  /** The presenter the ledger declares. */
  readonly presentador: string;
  /** The wrapper the ledger declares. */
  readonly wrapper: string;
  /** Whether the route EXISTS in the backend. */
  readonly registrado: boolean;
  /** WHY the route exists or does not exist. */
  readonly motivo: string;
  /** The permission the ledger declares. */
  readonly permiso: string;
}

/**
 * The ledger of the administration area, WITH the verification of the
 * registration.
 *
 * This object is the SINGLE SOURCE of the URLs of the area: a component, a
 * hook or a service never spells a path. To bind a route, the ONLY change is
 * `registrado: true` here, once the controller is registered in the backend.
 */
export const RUTAS_ADMIN = {
  /** `RT-IN-07` — the administrative list of the registrations. */
  inscripcionesLista: {
    ledger: "RT-IN-07",
    metodo: "get",
    ruta: "/administracion/inscripciones",
    presentador: "AdminInscripcionListaPresenter",
    wrapper: "PaginatedData[AdminInscripcionListItemOut]",
    registrado: true,
    motivo: "Registrada por AdminInscripcionController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-IN-08` — the administrative detail of a registration. */
  inscripcionDetalle: {
    ledger: "RT-IN-08",
    metodo: "get",
    ruta: "/administracion/inscripciones/{inscripcion_id}",
    presentador: "AdminInscripcionDetallePresenter",
    wrapper: "AdminInscripcionDetalleOut",
    registrado: true,
    motivo: "Registrada por AdminInscripcionController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-IN-09` — the administrative list of the teams. */
  equiposLista: {
    ledger: "RT-IN-09",
    metodo: "get",
    ruta: "/administracion/equipos",
    presentador: "AdminEquipoListaPresenter",
    wrapper: "PaginatedData[AdminEquipoListItemOut]",
    registrado: true,
    motivo: "Registrada por AdminEquipoController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-IN-10` — the administrative detail of a team. */
  equipoDetalle: {
    ledger: "RT-IN-10",
    metodo: "get",
    ruta: "/administracion/equipos/{equipo_id}",
    presentador: "AdminEquipoDetallePresenter",
    wrapper: "AdminEquipoDetalleOut",
    registrado: true,
    motivo: "Registrada por AdminEquipoController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-IN-11` — the administrative list of the participants. */
  participantesLista: {
    ledger: "RT-IN-11",
    metodo: "get",
    ruta: "/administracion/participantes",
    presentador: "AdminParticipanteListaPresenter",
    wrapper: "PaginatedData[AdminParticipanteListItemOut]",
    registrado: true,
    motivo: "Registrada por AdminParticipanteController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-PG-04` — the operational list of the payments (FROZEN in GOV-01). */
  pagosLista: {
    ledger: "RT-PG-04",
    metodo: "get",
    ruta: "/administracion/pagos",
    presentador: "AdminPagoPresenter",
    wrapper: "PaginatedData[AdminPagoListItemOut]",
    registrado: true,
    motivo: "Registrada por AdminPagoController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-PG-07` — the commercial detail of a payment. */
  pagoDetalle: {
    ledger: "RT-PG-07",
    metodo: "get",
    ruta: "/administracion/pagos/{compra_id}",
    presentador: "AdminPagoDetallePresenter",
    wrapper: "AdminPagoDetalleOut",
    registrado: true,
    motivo: "Registrada por AdminPagoController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-PG-06` — the attempts of the provider of a payment order. */
  pagoIntentos: {
    ledger: "RT-PG-06",
    metodo: "get",
    ruta: "/pagos/ordenes/{orden_id}/intentos",
    presentador: "PagoIntentosPresenter",
    wrapper: "PagoIntentosOut",
    registrado: false,
    motivo: "PagosController no expone /intentos: la ruta no existe.",
    permiso: "Titular del comprobador o Administrador",
  },
  /** `RT-PG-05` — the manual approval of a payment (FROZEN in GOV-01). */
  aprobarPagoManual: {
    ledger: "RT-PG-05",
    metodo: "post",
    ruta: "/administracion/pagos/{orden_pago_id}/aprobar-manual",
    presentador: "AdminOperacionPresenter",
    wrapper: "AdminPagoListItemOut",
    registrado: true,
    motivo: "Registrada por AdminPagoController en config/api.py.",
    permiso: "Administrador",
  },
  /**
   * The administrative withdrawal of a participant.
   *
   * The ledger does NOT declare it (`A0-UI04-04`): the registered
   * `DELETE /inscripciones/{id}/participantes/{participacion_id}` (`RT-IN-06`)
   * belongs to the RESPONSIBLE of his own inscription and the module does not
   * let the administrator group substitute for that titularidad
   * (`PoolOrchestrator._verificar_responsable`). It also carries no reason, so
   * it could not answer the audited action of the S-10.
   */
  retirarParticipante: {
    ledger: "A0-UI04-04",
    metodo: "delete",
    ruta: "/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}",
    presentador: "ParticipanteRetirarPresenter",
    wrapper: "PoolOut",
    registrado: true,
    motivo: "Registrada por AdminInscripcionController en config/api.py.",
    permiso: "Administrador + capacidad de escritura",
  },
  /**
   * The administrative add of an EXISTING participant to a team.
   *
   * The person is identified by her EXACT document: adding a participant
   * never creates a `Persona` (the administration area exposes no CRUD of
   * people).
   */
  agregarParticipanteEquipo: {
    ledger: "A0-ACP-01",
    metodo: "post",
    ruta: "/administracion/equipos/{equipo_id}/participantes",
    presentador: "AdminAsistidoPresenter",
    wrapper: "ParticipanteAsistidoOut",
    registrado: true,
    motivo: "Registrada por AdminAsistidoController en config/api.py.",
    permiso: "Administrador + admin.equipos.escribir",
  },
  /**
   * The assisted purchase of passes for a THIRD PARTY.
   *
   * The buyer is the CLIENT, never the administrator: the administrator is
   * the actor of the operation and the payment is settled with the canonical
   * manual approval.
   */
  comprarPaseCliente: {
    ledger: "A0-ACP-02",
    metodo: "post",
    ruta: "/administracion/pases/compras-cliente",
    presentador: "AdminAsistidoPresenter",
    wrapper: "CompraAsistidaOut",
    registrado: true,
    motivo: "Registrada por AdminAsistidoController en config/api.py.",
    permiso: "Administrador",
  },
  /**
   * The assisted order of the store for a THIRD PARTY.
   *
   * Same rule as the passes: the order and its purchase belong to the
   * client.
   */
  comprarPedidoCliente: {
    ledger: "A0-ACP-03",
    metodo: "post",
    ruta: "/administracion/marketplace/pedidos-cliente",
    presentador: "AdminAsistidoPresenter",
    wrapper: "CompraAsistidaOut",
    registrado: true,
    motivo: "Registrada por AdminAsistidoController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-ID-07` — the administrative list of the people. */
  personasLista: {
    ledger: "RT-ID-07",
    metodo: "get",
    ruta: "/administracion/personas",
    presentador: "AdminPersonaListaPresenter",
    wrapper: "PaginatedData[AdminPersonaListItemOut]",
    registrado: true,
    motivo: "Registrada por AdminPersonaController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-ID-08` — the administrative detail of a person. */
  personaDetalle: {
    ledger: "RT-ID-08",
    metodo: "get",
    ruta: "/administracion/personas/{persona_id}",
    presentador: "AdminPersonaDetallePresenter",
    wrapper: "AdminPersonaDetalleOut",
    registrado: true,
    motivo: "Registrada por AdminPersonaController en config/api.py.",
    permiso: "Administrador",
  },
  /**
   * `RT-ADM-01`: the operational summary of the edition (`ADM-01`).
   *
   * A NEW route: the provisional ledger `SH-05` had no row for the
   * transversal summary. It is declared by `XCT-02` and its ratification is
   * requested to A0.
   */
  resumen: {
    ledger: "RT-ADM-01",
    metodo: "get",
    ruta: "/administracion/resumen",
    presentador: "AdminResumenPresenter",
    wrapper: "ResumenOperativoOut",
    registrado: true,
    motivo: "Registrada por AdminController en config/api.py.",
    permiso: "Administrador",
  },
  /** `RT-ADM-02`: the audit trail of the sensitive actions. */
  auditoria: {
    ledger: "RT-ADM-02",
    metodo: "get",
    ruta: "/administracion/auditoria",
    presentador: "AdminAuditoriaPresenter",
    wrapper: "AuditoriaListadoOut",
    registrado: true,
    motivo: "Registrada por AdminController en config/api.py.",
    permiso: "Administrador",
  },
} as const satisfies Record<string, RutaAdmin>;

/** The id of a route of the ledger. */
export type RutaAdminId = keyof typeof RUTAS_ADMIN;

/**
 * A route of this area that does NOT exist in the backend.
 *
 * The service NEVER calls it: the guard rejects the route BEFORE the
 * transport, so no request leaves the browser for an URL that answers 404.
 */
export class ErrorRutaAdminNoRegistrada extends Error {
  constructor(public readonly ruta: RutaAdmin) {
    super(
      `La ruta ${ruta.ledger} (${ruta.metodo.toUpperCase()} ${ruta.ruta}) no está registrada en el backend: ${ruta.motivo}`,
    );
    this.name = "ErrorRutaAdminNoRegistrada";
  }
}

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is not a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY.
 */
export class ErrorContratoAdmin extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoAdmin";
  }
}

/** One field-level error, in the vocabulary of the form. */
export interface ErrorDeCampoAdmin {
  /** The path of the field, exactly as the backend publishes it. */
  campo: string;
  /** The stable code of the error of the field. */
  codigo: string;
  /** The public prose of the error of the field. */
  mensaje: string;
}

/**
 * A failure of the backend, with its HTTP status.
 *
 * The status is what the interface branches on (`403` is a permission answer,
 * `409` a conflict, `422` a validation answer) and NEVER on the machine code:
 * the catalogue of public codes is not closed.
 */
export class ErrorAdmin extends Error {
  constructor(
    /** The HTTP status of the answer, when the failure carries one. */
    public readonly status: number | undefined,
    /** The stable code of the failure. */
    public readonly codigo: string,
    /** The public prose of the failure, printed verbatim. */
    message: string,
    /** The field-level errors of a 422. */
    public readonly erroresDeCampo: readonly ErrorDeCampoAdmin[] = [],
  ) {
    super(message);
    this.name = "ErrorAdmin";
  }
}

/**
 * Builds the URL of a route of the ledger.
 *
 * It REJECTS a route that is not registered: the guard is the mechanism that
 * keeps this area from ever calling an URL that does not exist.
 */
export function urlDeRutaAdmin(
  ruta: RutaAdmin,
  parametros?: Record<string, string>,
): string {
  if (!ruta.registrado) {
    throw new ErrorRutaAdminNoRegistrada(ruta);
  }

  return ruta.ruta.replace(/\{(\w+)\}/g, (_coincidencia, clave: string) => {
    const valor = parametros?.[clave];

    if (valor === undefined || valor === "") {
      throw new Error(
        `Falta el parámetro «${clave}» de la ruta ${ruta.ledger}.`,
      );
    }

    return encodeURIComponent(valor);
  });
}

/**
 * Turns a failure of the transport into an `ErrorAdmin`.
 *
 * The public prose of the failure is the `error.message` of the frozen
 * envelope: the interface prints it verbatim and never translates it.
 */
function errorAdminDesde(error: unknown): ErrorAdmin {
  const fallo = error as
    | { response?: { status?: number; data?: unknown } }
    | undefined;
  const status = fallo?.response?.status;
  const envelope = adminErrorEnvelopeSchema.safeParse(fallo?.response?.data);

  if (envelope.success) {
    const detalle = envelope.data.error;

    return new ErrorAdmin(
      status,
      detalle.code,
      detalle.message,
      (detalle.field_errors ?? []).map((errorDeCampo) => ({
        campo: errorDeCampo.field,
        codigo: errorDeCampo.code,
        mensaje: errorDeCampo.message,
      })),
    );
  }

  return new ErrorAdmin(
    status,
    "ERROR_DE_TRANSPORTE",
    getErrorMessage(error),
    [],
  );
}

/**
 * The single way this area talks to the backend.
 *
 * It applies the rules of the envelope ONCE:
 *
 * 1. the route must be REGISTERED (the guard throws before the transport);
 * 2. a `204` is never parsed;
 * 3. the body is parsed with the Zod mirror of the wrapper;
 * 4. a body that does not comply is a LOUD failure;
 * 5. a failure becomes an `ErrorAdmin` with its status and its field errors.
 */
export async function pedirAdmin<T>(
  ruta: RutaAdmin,
  envelope: ZodType<{ success: boolean; data: T | null }>,
  opciones?: {
    /** The parameters of the QUERY string. */
    params?: Record<string, string | number | undefined>;
    /** The parameters of the PATH (`{inscripcion_id}`, `{compra_id}`, …). */
    pathParams?: Record<string, string>;
    /** The body of a mutation. */
    payload?: unknown;
  },
): Promise<T> {
  // El guard va ANTES del transporte: una ruta no registrada no sale nunca.
  const url = urlDeRutaAdmin(ruta, opciones?.pathParams);

  try {
    const { status, data } = await apiSend<unknown>(
      ruta.metodo,
      url,
      opciones?.payload,
      { params: opciones?.params },
    );

    if (status === 204 || data === null) {
      throw new ErrorContratoAdmin(
        "El servidor respondió sin contenido donde se esperaba un cuerpo.",
      );
    }

    const parseado = envelope.safeParse(data);

    if (!parseado.success) {
      throw new ErrorContratoAdmin(
        "La respuesta del servidor no cumple el contrato esperado.",
        parseado.error,
      );
    }

    if (!parseado.data.success || parseado.data.data === null) {
      throw new ErrorContratoAdmin("El servidor respondió sin datos.");
    }

    return parseado.data.data;
  } catch (error) {
    if (error instanceof ErrorContratoAdmin) {
      throw error;
    }

    throw errorAdminDesde(error);
  }
}
