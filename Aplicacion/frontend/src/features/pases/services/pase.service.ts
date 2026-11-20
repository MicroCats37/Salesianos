import type { Method } from "axios";
import type { ZodType } from "zod";
import { apiSend } from "@/lib/api";
import {
  asignarBeneficiarioSchema,
  beneficiarioRevocadoEnvelope,
  beneficiariosPaseEnvelope,
  CABECERA_TOKEN_PASE,
  catalogoPasesEnvelope,
  compraPaseCreadaEnvelope,
  compraPasesEnvelope,
  comprarPaseSchema,
  paseDetalleEnvelope,
  type AsignarBeneficiarioDatos,
  type BeneficiarioRevocado,
  type BeneficiariosPase,
  type CompraPaseCreada,
  type CompraPasesWire,
  type ComprarPaseDatos,
  type PaseDetalle,
  type CatalogoPases,
} from "../schemas/pase.schema";

/**
 * The ONE client of the pass domain.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/salesianos_fest/presentation/controllers/pase_controller.py`
 * → `PaseController`): a route that is not registered does not exist and is
 * never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-PS-01` | GET | `/pases` | `PaseCatalogoOut` |
 * | `RT-PS-02` | GET | `/pases/{pase_id}` | `PaseDetalleOut` |
 * | `RT-CM-02` | POST | `/pases/compras` | `CompraPaseCreadaOut` |
 * | `RT-PS-03` | GET | `/pases/compras/{compra_pase_id}` | `PaseCompraDetalleOut` |
 * | `RT-PS-04` | GET | `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiariosOut` |
 * | `RT-PS-05` | POST | `/pases/compras/{compra_pase_id}/beneficiarios` | `PaseBeneficiariosOut` |
 * | `RT-RT-03` | DELETE | `/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}` | `PaseBeneficiarioRevocadoOut` |
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the
 * HTTP client and of the rule that a `204` is never parsed.
 */

/** The base of every pass route. */
const BASE = "/pases";

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is NOT a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY, so this error
 * never hides behind a partial trust.
 */
export class ErrorContratoPase extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoPase";
  }
}

interface OpcionesPeticion {
  /** The body of the request. */
  payload?: unknown;
  /** The private token of the management link. */
  token?: string;
  /** The query parameters of the request. */
  params?: Record<string, string | number | undefined>;
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
  opciones: OpcionesPeticion = {},
): Promise<T> {
  const { status, data } = await apiSend<unknown>(
    method,
    url,
    opciones.payload,
    {
      params: opciones.params,
      headers: opciones.token
        ? { [CABECERA_TOKEN_PASE]: opciones.token }
        : undefined,
    },
  );

  if (status === 204 || data === null) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new ErrorContratoPase(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const parseado = envelope.safeParse(data);

  if (!parseado.success) {
    throw new ErrorContratoPase(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.error,
    );
  }

  if (!parseado.data.success || parseado.data.data === null) {
    throw new ErrorContratoPase("El servidor respondió sin datos.");
  }

  return parseado.data.data;
}

/**
 * The catalogue of passes of the edition in scope (`RT-PS-01`).
 *
 * The edition is resolved by the server when it is not declared. The
 * catalogue only publishes the passes with a current price: a pass without a
 * price is not offered.
 */
export function listarPases(params?: {
  edicion_id?: string;
}): Promise<CatalogoPases> {
  return pedir("get", BASE, catalogoPasesEnvelope, { params });
}

/** The detail of one pass (`RT-PS-02`). */
export function obtenerPase(paseId: string): Promise<PaseDetalle> {
  return pedir("get", `${BASE}/${paseId}`, paseDetalleEnvelope);
}

/**
 * The purchase of a batch of passes (`RT-CM-02`).
 *
 * The purchase may be a GUEST one: no account is needed and none is created.
 * The price is resolved and frozen by the server; the batch stays
 * `PENDIENTE` and it does not enable any pass until the payment is
 * confirmed.
 */
export function comprarPase(
  datos: ComprarPaseDatos,
): Promise<CompraPaseCreada> {
  return pedir("post", `${BASE}/compras`, compraPaseCreadaEnvelope, {
    payload: comprarPaseSchema.parse(datos),
  });
}

/**
 * The detail of a batch purchase (`RT-PS-03`).
 *
 * The link opens the batch with the PRIVATE TOKEN, carried by the
 * `X-Pase-Token` header. Without a valid credential the answer is 401 and
 * the batch is never exposed.
 */
export function obtenerCompra(
  compraPaseId: string,
  token: string,
): Promise<CompraPasesWire> {
  return pedir(
    "get",
    `${BASE}/compras/${compraPaseId}`,
    compraPasesEnvelope,
    { token },
  );
}

/** The rights granted in a batch (`RT-PS-04`). */
export function listarBeneficiarios(
  compraPaseId: string,
  token: string,
): Promise<BeneficiariosPase> {
  return pedir(
    "get",
    `${BASE}/compras/${compraPaseId}/beneficiarios`,
    beneficiariosPaseEnvelope,
    { token },
  );
}

/**
 * The assignment of a pass to a person (`RT-PS-05`).
 *
 * Only PAID capacity is assignable: a pending batch has no passes to share
 * (`RN-P02`). A right is not duplicated: the same person cannot hold two
 * active rights of the same pass (`RN-P07`).
 */
export function asignarBeneficiario(
  compraPaseId: string,
  token: string,
  datos: AsignarBeneficiarioDatos,
): Promise<BeneficiariosPase> {
  return pedir(
    "post",
    `${BASE}/compras/${compraPaseId}/beneficiarios`,
    beneficiariosPaseEnvelope,
    { token, payload: asignarBeneficiarioSchema.parse(datos) },
  );
}

/**
 * The revocation of an entry right (`RT-RT-03`).
 *
 * The revocation is PERMANENT, AUDITED and IDEMPOTENT: a right already
 * revoked answers 200 with `ya_revocado = true`, never an error.
 *
 * The reason travels as a QUERY PARAMETER: the frozen ledger declares this
 * route without an input schema.
 */
export function revocarBeneficiario(
  compraPaseId: string,
  token: string,
  personaId: string,
  motivo?: string,
): Promise<BeneficiarioRevocado> {
  return pedir(
    "delete",
    `${BASE}/compras/${compraPaseId}/beneficiarios/${personaId}`,
    beneficiarioRevocadoEnvelope,
    { token, params: { motivo: motivo ?? undefined } },
  );
}
