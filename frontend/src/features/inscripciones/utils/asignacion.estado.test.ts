/**
 * Focused tests for the assignment eligibility mapping.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/inscripciones/utils/asignacion.estado.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./asignacion.estado.ts";
const asignacion = (await import(specifier)) as {
  asignacionEstadoDeCandidato: (candidato: {
    asignable: boolean;
    ya_en_disciplina: boolean;
    tiene_cupo_activo: boolean;
  }) => string;
  candidatoEsSeleccionable: (candidato: {
    asignable: boolean;
    ya_en_disciplina: boolean;
    tiene_cupo_activo: boolean;
  }) => boolean;
};

// ── The backend verdict wins ─────────────────────────────────────────────────

test("un candidato asignable con cupo activo es 'asignable'", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: true,
      ya_en_disciplina: false,
      tiene_cupo_activo: true,
    }),
    "asignable",
  );
});

test("un candidato sin cupo es 'sin_cupo'", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: false,
      ya_en_disciplina: false,
      tiene_cupo_activo: false,
    }),
    "sin_cupo",
  );
});

// ── A rule block is NOT a commercial block ───────────────────────────────────
//
// The backend can block a candidate that HAS a paid cup (it does not play in
// the target discipline yet). That block comes from a domain rule — the
// frontend never knows which one, it only renders the backend reason.

test("un candidato con cupo bloqueado por el backend es 'no_asignable'", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: false,
      ya_en_disciplina: false,
      tiene_cupo_activo: true,
    }),
    "no_asignable",
  );
});

test("'no_asignable' no es seleccionable", () => {
  assert.equal(
    asignacion.candidatoEsSeleccionable({
      asignable: false,
      ya_en_disciplina: false,
      tiene_cupo_activo: true,
    }),
    false,
  );
});

// ── R11 wins over the commercial block ───────────────────────────────────────

test("un candidato que ya juega en la disciplina es 'ya_en_disciplina'", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: false,
      ya_en_disciplina: true,
      tiene_cupo_activo: true,
    }),
    "ya_en_disciplina",
  );
});

test("R11 gana aunque el candidato no tenga cupo", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: false,
      ya_en_disciplina: true,
      tiene_cupo_activo: false,
    }),
    "ya_en_disciplina",
  );
});

// ── Safe defaults ────────────────────────────────────────────────────────────

test("payload contradictorio (asignable sin cupo) queda bloqueado", () => {
  assert.equal(
    asignacion.asignacionEstadoDeCandidato({
      asignable: true,
      ya_en_disciplina: false,
      tiene_cupo_activo: false,
    }),
    "sin_cupo",
  );
});

test("solo 'asignable' es seleccionable", () => {
  assert.equal(
    asignacion.candidatoEsSeleccionable({
      asignable: true,
      ya_en_disciplina: false,
      tiene_cupo_activo: true,
    }),
    true,
  );
  for (const candidato of [
    { asignable: false, ya_en_disciplina: false, tiene_cupo_activo: false },
    { asignable: false, ya_en_disciplina: true, tiene_cupo_activo: true },
    { asignable: true, ya_en_disciplina: false, tiene_cupo_activo: false },
    { asignable: false, ya_en_disciplina: false, tiene_cupo_activo: true },
  ]) {
    assert.equal(asignacion.candidatoEsSeleccionable(candidato), false);
  }
});
