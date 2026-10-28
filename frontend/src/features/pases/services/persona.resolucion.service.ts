"use client";

import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import {
  type PersonaResuelta,
  personaResueltaEnvelopeSchema,
} from "../schemas";
import { pedir } from "./pase.http";

/**
 * PersonaResolucionService — the EXACT lookup of an existing `Persona`.
 *
 * Endpoint:
 *   GET /api/personas/resolver?tipo_documento=DNI&numero_documento=12345678
 *
 * It is NOT the external document lookup (`/personas/busqueda/{documento}`):
 * that one queries RENIEC/SUNAT and is public. This one resolves the INTERNAL
 * id of a person that already exists in the application, and it requires a
 * session.
 *
 * The lookup NEVER creates a person and NEVER lists people: the match is
 * exact.
 */

/** Normalize the document type exactly like the backend does. */
export function normalizarTipoDocumento(tipoDocumento: string): string {
  return (tipoDocumento ?? "").trim().toUpperCase();
}

/** Normalize the document number exactly like the backend does. */
export function normalizarNumeroDocumento(numeroDocumento: string): string {
  return (numeroDocumento ?? "").trim();
}

/**
 * Resolve the person that matches the document EXACTLY.
 *
 * Raises `ApiQueryError` with the status 404 when no registered person
 * matches: the caller renders the "not found" state instead of a failure.
 */
export async function resolverPersona(
  tipoDocumento: string,
  numeroDocumento: string,
): Promise<PersonaResuelta> {
  const envelope = await pedir(
    () =>
      api.get("/personas/resolver", {
        params: {
          tipo_documento: normalizarTipoDocumento(tipoDocumento),
          numero_documento: normalizarNumeroDocumento(numeroDocumento),
        },
      }),
    (datos) => personaResueltaEnvelopeSchema.parse(datos),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se encontró una persona registrada con ese documento.",
      undefined,
    );
  }

  return envelope.data;
}
