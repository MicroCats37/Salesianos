/**
 * Focused tests for the pool-first UI mapping.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/inscripciones/utils/pool.primero.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./pool.primero.ts";
const primero = (await import(specifier)) as {
  poolCtaDe: (contexto: string) => { label: string; description: string };
  poolGuiaEquipoVacio: () => { titulo: string; descripcion: string };
  poolGuiaSelectorVacio: () => { titulo: string; descripcion: string };
};

// ── The CTA is the single entry point ────────────────────────────────────────

test("el CTA de cabecera se llama 'Agregar participante'", () => {
  assert.equal(primero.poolCtaDe("cabecera").label, "Agregar participante");
});

test("el CTA del pool vacío propone el primer participante", () => {
  assert.equal(
    primero.poolCtaDe("vacio").label,
    "Agregar el primer participante",
  );
});

test("el CTA nunca habla de equipos: sólo de registro en el pool", () => {
  for (const contexto of ["cabecera", "vacio"]) {
    const cta = primero.poolCtaDe(contexto);
    const texto = `${cta.label} ${cta.description}`.toLowerCase();
    assert.ok(
      texto.includes("pool"),
      `el CTA debe mencionar el pool: ${texto}`,
    );
    assert.ok(
      !texto.includes("al equipo"),
      `el CTA no debe prometer una asignación directa: ${texto}`,
    );
  }
});

test("el CTA explica el paso siguiente (asignar con el selector)", () => {
  assert.match(primero.poolCtaDe("cabecera").description, /selector/i);
});

// ── The empty states guide back to the pool ──────────────────────────────────

test("el equipo vacío guía al pool y luego al selector", () => {
  const guia = primero.poolGuiaEquipoVacio();
  const texto = `${guia.titulo} ${guia.descripcion}`.toLowerCase();
  assert.ok(texto.includes("pool"), `debe mencionar el pool: ${texto}`);
  assert.ok(texto.includes("selector"), `debe mencionar el selector: ${texto}`);
  assert.ok(
    texto.indexOf("pool") < texto.indexOf("selector"),
    "el pool es el primer paso y el selector el segundo",
  );
});

test("el selector vacío guía al pool", () => {
  const guia = primero.poolGuiaSelectorVacio();
  assert.equal(
    guia.titulo,
    "No hay participantes que puedan unirse a este equipo.",
  );
  assert.match(guia.descripcion, /pool/i);
  assert.match(guia.descripcion, /agregar participante/i);
});
