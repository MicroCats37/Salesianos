import { apiSend } from "@/lib/api";
import { apiResponseSchema } from "@/types/api.types";
import {
  type DocumentoConsulta,
  DocumentoConsultaSchema,
  type Persona,
  type PersonaConfirmarIn,
  PersonaConfirmarInSchema,
  type PersonaResolverIn,
  PersonaResolverInSchema,
  type PersonaResuelta,
  PersonaResueltaSchema,
  PersonaSchema,
} from "../schemas/identidad.schema";

/**
 * The routes of the identity dataset (the `usuarios` module).
 *
 * All three are REGISTERED in `Aplicacion/backend/config/api.py`
 * (`PersonaController`):
 *
 * - `RT-ID-01` — `GET /api/personas/busqueda/{documento}` (public).
 * - `RT-ID-02` — `POST /api/personas/resolver` (session required).
 * - `RT-ID-03` — `POST /api/personas/confirmar` (session required).
 *
 * The paths are written WITHOUT the `/api` prefix because the transport owner
 * (`src/lib/api.ts`) already carries the namespace of the API.
 */
export const PERSONA_BUSQUEDA_PATH = "/personas/busqueda";
export const PERSONA_RESOLVER_PATH = "/personas/resolver";
export const PERSONA_CONFIRMAR_PATH = "/personas/confirmar";

/** The envelopes of the three routes, with the EXACT mirror of their wrapper. */
const documentoConsultaResponseSchema = apiResponseSchema(
  DocumentoConsultaSchema,
);
const personaResueltaResponseSchema = apiResponseSchema(PersonaResueltaSchema);
const personaResponseSchema = apiResponseSchema(PersonaSchema);

/**
 * The answer of a route of this dataset, parsed LOUDLY.
 *
 * An answer that does not match the mirror of the presenter is a FAILURE, not
 * a partially trusted value (`contract/api-wrapper-presenter-contract.md` §7).
 */
function leerRespuesta<T>(
  envelope: {
    success: boolean;
    data: T | null;
    error?: { message: string } | null;
  },
  mensaje: string,
): T {
  if (!envelope.success) {
    throw new Error(envelope.error?.message ?? mensaje);
  }

  if (envelope.data === null) {
    throw new Error(`${mensaje} La respuesta vino sin contenido.`);
  }

  return envelope.data;
}

/**
 * `RT-ID-01` — consults a document in the EXTERNAL identity source.
 *
 * The source decides which kind of document it recognises and it publishes
 * ONLY the civil identity: no internal identifier travels in this answer.
 */
export async function consultarDocumento(
  documento: string,
): Promise<DocumentoConsulta> {
  const { data } = await apiSend<unknown>(
    "GET",
    `${PERSONA_BUSQUEDA_PATH}/${encodeURIComponent(documento)}`,
  );

  const envelope = documentoConsultaResponseSchema.parse(data);

  return leerRespuesta(envelope, "No se pudo consultar el documento.");
}

/**
 * `RT-ID-02` — resolves an identity, LOCAL FIRST.
 *
 * When the person is already registered the answer carries its `persona_id`
 * and the external source is NOT consulted. When it is not, the answer carries
 * the preloaded data with `persona_id` null: the identity is NOT persisted
 * yet. This route does NOT authorise anything.
 */
export async function resolverPersona(
  payload: PersonaResolverIn,
): Promise<PersonaResuelta> {
  const cuerpo = PersonaResolverInSchema.parse(payload);

  const { data } = await apiSend<unknown>(
    "POST",
    PERSONA_RESOLVER_PATH,
    cuerpo,
  );

  const envelope = personaResueltaResponseSchema.parse(data);

  return leerRespuesta(envelope, "No se pudo resolver la identidad.");
}

/**
 * `RT-ID-03` — confirms and persists an identity.
 *
 * This is the operation that PERSISTS the `Persona`. It does NOT create an
 * account: the birth of an account is explicit and apart (`FR-03` §1.2).
 *
 * The error of this route travels AS IT IS: the field errors of a `422` and
 * the conflict of a `409` have to reach the control they belong to, and the
 * shared error handler (`handleApiError`) reads them from the response of the
 * original request.
 */
export async function confirmarPersona(
  payload: PersonaConfirmarIn,
): Promise<Persona> {
  const cuerpo = PersonaConfirmarInSchema.parse(payload);

  const { data } = await apiSend<unknown>(
    "POST",
    PERSONA_CONFIRMAR_PATH,
    cuerpo,
  );

  const envelope = personaResponseSchema.parse(data);

  return leerRespuesta(envelope, "No se pudo confirmar la identidad.");
}
