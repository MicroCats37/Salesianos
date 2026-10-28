"use client";

import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import { buildApiPayload } from "@/utils/payload-builder";
import {
  type PaseBeneficiarioRevocado,
  type PaseBeneficiarioRevocarIn,
  type PaseBeneficiariosAsignados,
  type PaseBeneficiariosAsignarIn,
  type PaseBeneficiariosLista,
  paseBeneficiarioRevocadoEnvelopeSchema,
  paseBeneficiarioRevocarInSchema,
  paseBeneficiariosAsignadosEnvelopeSchema,
  paseBeneficiariosAsignarInSchema,
  paseBeneficiariosListaEnvelopeSchema,
} from "../schemas";
import { pedir } from "./pase.http";

/**
 * PaseBeneficiarioService — the nominative rights of a paid pass batch.
 *
 * Endpoints:
 *   GET    /api/pases/compras/{compra_id}/beneficiarios
 *   POST   /api/pases/compras/{compra_id}/beneficiarios
 *   DELETE /api/pases/compras/{compra_id}/beneficiarios/{persona_id}
 *
 * The API NEVER creates a person out of free text: every id is the UUID of an
 * EXISTING `Persona` that the client already resolved.
 */

/** Validate the body of the assignment before it leaves the browser. */
function construirCuerpoAsignacion(
  beneficiarioIds: string[],
): PaseBeneficiariosAsignarIn {
  const resultado = paseBeneficiariosAsignarInSchema.safeParse({
    beneficiario_ids: beneficiarioIds,
  });

  if (!resultado.success) {
    throw new ApiQueryError(
      "No se pueden asignar esas personas al lote de pases.",
      undefined,
    );
  }

  return resultado.data;
}

/** Validate the motive of the revocation before it leaves the browser. */
function construirCuerpoRevocacion(motivo: string): PaseBeneficiarioRevocarIn {
  const resultado = paseBeneficiarioRevocarInSchema.safeParse({ motivo });

  if (!resultado.success) {
    throw new ApiQueryError(
      "La revocación necesita un motivo obligatorio.",
      undefined,
    );
  }

  return resultado.data;
}

/**
 * The rights of a batch, with the immutable slot accounting.
 *
 * Only the buyer (`Compra.responsable`) may read them.
 */
export async function fetchBeneficiariosCompra(
  compraId: string,
): Promise<PaseBeneficiariosLista> {
  const envelope = await pedir(
    () => api.get(`/pases/compras/${compraId}/beneficiarios`),
    (datos) => paseBeneficiariosListaEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudieron consultar los beneficiarios del lote.",
      undefined,
    );
  }

  return envelope.data;
}

/**
 * Assign persons to the free slots of a batch.
 *
 * The purchase MUST be paid and the caller MUST be the buyer. The slots are
 * immutable: the lowest free ones are allocated and a revoked slot is never
 * restored.
 */
export async function asignarBeneficiariosCompra(
  compraId: string,
  beneficiarioIds: string[],
): Promise<PaseBeneficiariosAsignados> {
  const cuerpo = construirCuerpoAsignacion(beneficiarioIds);

  const envelope = await pedir(
    () =>
      api.post(
        `/pases/compras/${compraId}/beneficiarios`,
        buildApiPayload(cuerpo),
      ),
    (datos) => paseBeneficiariosAsignadosEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudieron asignar los beneficiarios.",
      undefined,
    );
  }

  return envelope.data;
}

/**
 * Revoke a right PERMANENTLY.
 *
 * The motive is mandatory and audited. The revocation is NOT a transfer: the
 * slot is consumed forever and the right never moves to somebody else.
 */
export async function revocarBeneficiarioCompra(
  compraId: string,
  personaId: string,
  motivo: string,
): Promise<PaseBeneficiarioRevocado> {
  const cuerpo = construirCuerpoRevocacion(motivo);

  const envelope = await pedir(
    () =>
      api.delete(`/pases/compras/${compraId}/beneficiarios/${personaId}`, {
        data: buildApiPayload(cuerpo),
      }),
    (datos) => paseBeneficiarioRevocadoEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudo revocar el pase del beneficiario.",
      undefined,
    );
  }

  return envelope.data;
}
