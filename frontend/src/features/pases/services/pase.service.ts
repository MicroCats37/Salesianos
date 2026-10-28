"use client";

import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import { buildApiPayload } from "@/utils/payload-builder";
import {
  type PaseCatalogo,
  type PaseCompraCreada,
  type PaseCompraEstado,
  type PaseComprarIn,
  paseCatalogoEnvelopeSchema,
  paseCompraCreadaEnvelopeSchema,
  paseCompraEstadoEnvelopeSchema,
  paseComprarInSchema,
} from "../schemas";
import { pedir } from "./pase.http";

/**
 * PaseService — the public catalogue of the party passes and the purchase of
 * a batch of them.
 *
 * Endpoints:
 *   GET  /api/pases/                    - Public catalogue of the active passes
 *   POST /api/pases/comprar              - Buy a batch of passes (authenticated)
 *   GET  /api/pases/compras/{compra_id}  - State of a pass purchase (owner only)
 *
 * The catalogue is PUBLIC and the purchase is OWNER-scoped: the browser never
 * sends a price nor a total — the server freezes them.
 */

/**
 * Query keys of the pass feature.
 *
 * The catalogue is keyed by its own prefix and every purchase by its own id:
 * paying one batch never invalidates the state of another one.
 */
export const paseQueryKeys = {
  /** The public catalogue of the passes. */
  catalogo: ["pases", "catalogo"] as const,
  /** The state of ONE purchase. */
  compra: (compraId: string) => ["pases", "compra", compraId] as const,
  /** The nominative rights of ONE purchase. */
  beneficiarios: (compraId: string) =>
    ["pases", "beneficiarios", compraId] as const,
};

/** Validate the body of the purchase before it leaves the browser. */
function construirCuerpoCompra(payload: PaseComprarIn): PaseComprarIn {
  const resultado = paseComprarInSchema.safeParse(payload);
  if (!resultado.success) {
    throw new ApiQueryError(
      "La compra no se puede registrar con estos datos.",
      undefined,
    );
  }
  return resultado.data;
}

/**
 * The public catalogue of the passes that can be bought right now.
 *
 * The catalogue is EMPTY while the rollout is off or when there is no active
 * pass: an unpublished catalogue is never leaked.
 */
export async function fetchCatalogoPases(): Promise<PaseCatalogo[]> {
  const envelope = await pedir(
    () => api.get("/pases/"),
    (datos) => paseCatalogoEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudo cargar el catálogo de pases.",
      undefined,
    );
  }

  return envelope.data;
}

/**
 * Buy a batch of passes.
 *
 * The body carries ONLY the pass and the quantity: the price and the total
 * are computed and frozen by the server.
 */
export async function crearCompraPase(
  payload: PaseComprarIn,
): Promise<PaseCompraCreada> {
  const cuerpo = construirCuerpoCompra(payload);

  const envelope = await pedir(
    () => api.post("/pases/comprar", buildApiPayload(cuerpo)),
    (datos) => paseCompraCreadaEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudo registrar la compra de pases.",
      undefined,
    );
  }

  return envelope.data;
}

/**
 * The state of a pass purchase.
 *
 * Only the buyer (`Compra.responsable`) may read it.
 */
export async function fetchCompraPase(
  compraId: string,
): Promise<PaseCompraEstado> {
  const envelope = await pedir(
    () => api.get(`/pases/compras/${compraId}`),
    (datos) => paseCompraEstadoEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudo consultar la compra de pases.",
      undefined,
    );
  }

  return envelope.data;
}
