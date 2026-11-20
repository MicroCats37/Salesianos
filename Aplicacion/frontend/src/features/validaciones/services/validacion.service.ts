import type { Method } from "axios";
import type { ZodType } from "zod";
import { apiSend } from "@/lib/api";
import {
  type ConfirmarTicketDatos,
  confirmarTicketSchema,
  previewTicketSchema,
  type TicketConfirmado,
  type TicketPreview,
  ticketConfirmadoEnvelope,
  ticketPreviewEnvelope,
} from "../schemas/validacion.schema";

/**
 * The ONE client of the validation area.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/validaciones/presentation/controllers/validacion_controller.py`
 * → `ValidacionController`): a route that is not registered does not exist and
 * is never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-RT-01` | POST | `/validaciones/preview` | `TicketPreviewOut` |
 * | `RT-RT-02` | POST | `/validaciones/confirmar` | `TicketConfirmadoOut` |
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 *
 * The two operations share the CLIENT and nothing else: the entry and the
 * delivery are two screens with two different decisions, and the backend
 * resolves each one against its own owner.
 */

/** The base of every validation route. */
const BASE = "/validaciones";

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is NOT a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY, so this error never
 * hides behind a partial trust.
 */
export class ErrorContratoValidacion extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoValidacion";
  }
}

/**
 * The single way this feature talks to the backend.
 *
 * It applies the rules of the envelope ONCE: the `204` is never parsed, the
 * body is parsed with the Zod mirror of the wrapper and a body that does not
 * comply is a loud failure.
 */
async function pedir<T>(
  method: Method,
  url: string,
  envelope: ZodType<{ success: boolean; data: T | null }>,
  payload?: unknown,
): Promise<T> {
  const { status, data } = await apiSend<unknown>(method, url, payload);

  if (status === 204 || data === null) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new ErrorContratoValidacion(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const parseado = envelope.safeParse(data);

  if (!parseado.success) {
    throw new ErrorContratoValidacion(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.error,
    );
  }

  if (!parseado.data.success || parseado.data.data === null) {
    throw new ErrorContratoValidacion("El servidor respondió sin datos.");
  }

  return parseado.data.data;
}

/**
 * The CHECK of a credential (`RT-RT-01`).
 *
 * It does NOT consume: the backend publishes what the right's owner says and
 * the credential stays intact (`RN-P06`).
 */
export function previewTicket(codigo: string): Promise<TicketPreview> {
  return pedir(
    "post",
    `${BASE}/preview`,
    ticketPreviewEnvelope,
    previewTicketSchema.parse({ codigo }),
  );
}

/**
 * The CONFIRMATION of a credential (`RT-RT-02`).
 *
 * It consumes, it is ATOMIC and it is IDEMPOTENT: repeating the same
 * `idempotency_key` returns the same record and never consumes twice
 * (`FR-04` §2.2).
 */
export function confirmarTicket(
  datos: ConfirmarTicketDatos,
): Promise<TicketConfirmado> {
  return pedir(
    "post",
    `${BASE}/confirmar`,
    ticketConfirmadoEnvelope,
    confirmarTicketSchema.parse(datos),
  );
}
