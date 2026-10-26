/**
 * Focused tests for the pool preregistration payloads.
 *
 * The invariant under test is the pool-first rule: NO preregistration payload
 * may carry a team, because the absence of `equipo_id` is exactly what makes
 * the backend create a preregistration (and claim the paid cup) instead of a
 * direct team placement.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/inscripciones/utils/pool.preregistro.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./pool.preregistro.ts";
const preregistro = (await import(specifier)) as {
  buildPreregistroPayload: (input: {
    tipoDocumento: string;
    numeroDocumento: string;
    nombres: string;
    apellidos: string;
    genero: string;
    telefono?: string | null;
    whatsapp?: string | null;
  }) => Record<string, unknown>;
  buildPreregistroSelfPayload: (personaId: string) => Record<string, unknown>;
};

const PERSONA = {
  tipoDocumento: "DNI",
  numeroDocumento: "12345678",
  nombres: "Ana",
  apellidos: "Torres",
  genero: "F",
  telefono: "999888777",
  whatsapp: null,
};

// ── The pool-first invariant ─────────────────────────────────────────────────

test("el preregistro de una persona nueva NO lleva equipo", () => {
  const payload = preregistro.buildPreregistroPayload(PERSONA);
  assert.equal(
    "equipo_id" in payload,
    false,
    "un preregistro con equipo_id crearía una participación directa",
  );
});

test("el preregistro propio NO lleva equipo", () => {
  const payload = preregistro.buildPreregistroSelfPayload("persona-uuid");
  assert.equal(
    "equipo_id" in payload,
    false,
    "el auto-registro es pool-first: la asignación la hace el selector",
  );
});

// ── The payloads carry the right identity ────────────────────────────────────

test("el preregistro de una persona nueva envía persona_data", () => {
  const payload = preregistro.buildPreregistroPayload(PERSONA);
  assert.equal("persona_id" in payload, false);

  const personaData = payload.persona_data as Record<string, unknown>;
  assert.equal(personaData.numero_documento, "12345678");
  assert.equal(personaData.nombres, "Ana");
  assert.equal(personaData.apellidos, "Torres");
  assert.equal(personaData.tipo_documento, "DNI");
  assert.equal(personaData.genero, "F");
});

test("el preregistro propio reutiliza la persona existente (persona_id)", () => {
  const payload = preregistro.buildPreregistroSelfPayload("persona-uuid");
  assert.equal(payload.persona_id, "persona-uuid");
  assert.equal("persona_data" in payload, false);
});
