import type { Method } from "axios";
import type { ZodType } from "zod";
import { getErrorMessage } from "@/errors";
import { adminErrorEnvelopeSchema } from "@/features/admin/operaciones/schemas/operaciones.schema";
import {
  ErrorAdmin,
  ErrorContratoAdmin,
  type ErrorDeCampoAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { apiSend } from "@/lib/api";
import {
  type AdminCortesia,
  type AdminCortesiaRevocada,
  adminCortesiaEnvelope,
  adminCortesiaRevocadaEnvelope,
  adminCortesiasListaEnvelope,
  type EmitirTicket,
  emitirTicketSchema,
  type OtorgarCortesia,
  otorgarCortesiaSchema,
  type PaginaCortesias,
  type RevocarCortesia,
  revocarCortesiaSchema,
  type TicketEmitido,
  ticketEmitidoEnvelope,
} from "../schemas/admin.pase.schema";
import type { ParamsListaCortesias } from "../utils/admin.pase.claves.utils";

/**
 * The client of the ADMINISTRATIVE PASSES: the courtesies and the credential
 * of the door.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-PS-07` | GET | `/administracion/pases/cortesias` | `PaginatedData[AdminCortesiaListItemOut]` |
 * | `RT-PS-08` | POST | `/administracion/pases/cortesias` | `AdminCortesiaOut` (201) |
 * | `RT-PS-09` | POST | `/administracion/pases/cortesias/{cortesia_id}/revocar` | `AdminCortesiaRevocadaOut` (200) |
 * | `RT-VT-03` | POST | `/validaciones/tickets` | `TicketEmitidoOut` (201) |
 *
 * ## Why the routes are LOCAL
 *
 * The ledger of the administration (`RUTAS_ADMIN`) belongs to another owner
 * and it does not declare these four routes: this module declares them HERE,
 * as constants, and it never spells a path in a component.
 *
 * ## The transport
 *
 * `apiSend` (`src/lib/api.ts`) is the single owner of the HTTP client and of
 * the rule that a `204` is NEVER parsed.
 */

/** The base of the routes of the courtesies. */
export const RUTA_CORTESIAS = "/administracion/pases/cortesias";

/** The base of the routes of the tickets of the door. */
export const RUTA_TICKETS = "/validaciones/tickets";

/** The route of the list of the courtesies. */
export function rutaCortesias(): string {
  return RUTA_CORTESIAS;
}

/** The route of the revocation of ONE courtesy. */
export function rutaRevocarCortesia(cortesiaId: string): string {
  return `${RUTA_CORTESIAS}/${cortesiaId}/revocar`;
}

/** The route of the issue of the credential of the door. */
export function rutaEmitirCredencial(): string {
  return RUTA_TICKETS;
}

/**
 * Turns a failure of the transport into an `ErrorAdmin`.
 *
 * The public prose of the failure is the `error.message` of the frozen
 * envelope: the interface prints it verbatim and never translates it.
 *
 * The raw answer travels WITH the error so that `handleApiError` can map the
 * `field_errors` of a 422 to the control they belong to: the form owns the
 * field errors, never the component.
 */
function errorAdminDesde(error: unknown): ErrorAdmin {
  const fallo = error as
    | { response?: { status?: number; data?: unknown } }
    | undefined;
  const status = fallo?.response?.status;
  const envelope = adminErrorEnvelopeSchema.safeParse(fallo?.response?.data);

  if (envelope.success) {
    const detalle = envelope.data.error;
    const erroresDeCampo: ErrorDeCampoAdmin[] = (
      detalle.field_errors ?? []
    ).map((errorDeCampo) => ({
      campo: errorDeCampo.field,
      codigo: errorDeCampo.code,
      mensaje: errorDeCampo.message,
    }));

    const adminError = new ErrorAdmin(
      status,
      detalle.code,
      detalle.message,
      erroresDeCampo,
    );

    (adminError as { response?: unknown }).response = fallo?.response;

    return adminError;
  }

  return new ErrorAdmin(
    status,
    "ERROR_DE_TRANSPORTE",
    getErrorMessage(error),
    [],
  );
}

/**
 * The single way this feature talks to the backend.
 *
 * It applies the rules of the envelope ONCE: the `204` is never parsed, the
 * body is parsed with the Zod mirror of the wrapper and a body that does not
 * comply is a LOUD failure.
 */
async function pedir<T>(
  metodo: Method,
  url: string,
  envelope: ZodType<{ success: boolean; data: T | null }>,
  opciones: {
    /** The body of the request. */
    payload?: unknown;
    /** The parameters of the query string. */
    params?: Record<string, string | number | undefined>;
  } = {},
): Promise<T> {
  try {
    const { status, data } = await apiSend<unknown>(
      metodo,
      url,
      opciones.payload,
      { params: opciones.params },
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

/**
 * The list of the courtesies of the edition in scope.
 *
 * The list NEVER publishes the token of the management of a purchase nor the
 * detail of a payment.
 */
export async function listarCortesias(
  params?: ParamsListaCortesias,
): Promise<PaginaCortesias> {
  const pagina = await pedir(
    "get",
    rutaCortesias(),
    adminCortesiasListaEnvelope,
    {
      params: {
        edicion_id: params?.edicion_id,
        estado: params?.estado,
        page: params?.page,
        page_size: params?.page_size,
      },
    },
  );

  return pagina;
}

/**
 * The grant of a courtesy.
 *
 * The command carries NO amount and NO currency: a courtesy has no financial
 * facts at all (`R4`). The identity travels as DATA and the backend resolves
 * it against the padrón.
 */
export async function otorgarCortesia(
  payload: OtorgarCortesia,
): Promise<AdminCortesia> {
  const cuerpo = otorgarCortesiaSchema.parse(payload);

  return pedir("post", rutaCortesias(), adminCortesiaEnvelope, {
    payload: {
      edicion_id: cuerpo.edicion_id,
      pase_id: cuerpo.pase_id,
      tipo_documento: cuerpo.tipo_documento,
      numero_documento: cuerpo.numero_documento,
      nombres: cuerpo.nombres,
      apellidos: cuerpo.apellidos,
      motivo: cuerpo.motivo,
    },
  });
}

/**
 * The revocation of a courtesy.
 *
 * It is AUDITED (the reason is mandatory) and IDEMPOTENT: a second
 * revocation answers `200` with `ya_revocado = true`, never an error.
 */
export async function revocarCortesia(
  cortesiaId: string,
  payload: RevocarCortesia,
): Promise<AdminCortesiaRevocada> {
  const cuerpo = revocarCortesiaSchema.parse(payload);

  return pedir(
    "post",
    rutaRevocarCortesia(cortesiaId),
    adminCortesiaRevocadaEnvelope,
    { payload: { motivo: cuerpo.motivo } },
  );
}

/**
 * The issue of the credential of the door.
 *
 * The browser declares ONLY the right: the type of the right and the
 * operation of the ticket are DERIVED by the server. The code travels in
 * this answer and NOWHERE else: it is never listed, never audited and never
 * cached.
 */
export async function emitirCredencial(
  payload: EmitirTicket,
): Promise<TicketEmitido> {
  const cuerpo = emitirTicketSchema.parse(payload);

  return pedir("post", rutaEmitirCredencial(), ticketEmitidoEnvelope, {
    payload: { derecho_id: cuerpo.derecho_id },
  });
}
