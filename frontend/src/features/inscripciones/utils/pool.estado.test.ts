/**
 * Focused tests for the pool eligibility mapping.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/inscripciones/utils/pool.estado.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./pool.estado.ts";
const pool = (await import(specifier)) as {
  poolEstadoDeEntrada: (entry: {
    tiene_cupo_activo: boolean;
    estado_pool?: string | null;
    motivo_bloqueo: string | null;
  }) => string;
  poolEsAsignable: (
    entry: {
      tiene_cupo_activo: boolean;
      estado_pool?: string | null;
      motivo_bloqueo: string | null;
    },
    sinDestino?: boolean,
  ) => boolean;
  ESTADO_POOL_LISTO: string;
  ESTADO_POOL_ESPERANDO_PAGO: string;
  ESTADO_POOL_SIN_CAPACIDAD: string;
  ESTADO_POOL_CUPO_POR_ASIGNAR: string;
  MOTIVO_ESPERANDO_PAGO: string;
  MOTIVO_SIN_CAPACIDAD: string;
  MOTIVO_CUPO_POR_ASIGNAR: string;
};

// ── The typed discriminator decides the state ─────────────────────────────────

test("cupo activo siempre es 'listo'", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: true,
      estado_pool: pool.ESTADO_POOL_LISTO,
      motivo_bloqueo: null,
    }),
    "listo",
  );
});

test("estado_pool ESPERANDO_PAGO -> esperando_pago", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: pool.ESTADO_POOL_ESPERANDO_PAGO,
      motivo_bloqueo: pool.MOTIVO_ESPERANDO_PAGO,
    }),
    "esperando_pago",
  );
});

test("estado_pool SIN_CAPACIDAD -> sin_capacidad", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: pool.ESTADO_POOL_SIN_CAPACIDAD,
      motivo_bloqueo: pool.MOTIVO_SIN_CAPACIDAD,
    }),
    "sin_capacidad",
  );
});

test("estado_pool CUPO_POR_ASIGNAR -> cupo_por_asignar", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: pool.ESTADO_POOL_CUPO_POR_ASIGNAR,
      motivo_bloqueo: pool.MOTIVO_CUPO_POR_ASIGNAR,
    }),
    "cupo_por_asignar",
  );
});

// ── The paid capacity must NEVER be reported as "esperando pago" ─────────────

test("capacidad pagada disponible no se reporta como 'esperando_pago'", () => {
  const estado = pool.poolEstadoDeEntrada({
    tiene_cupo_activo: false,
    estado_pool: pool.ESTADO_POOL_CUPO_POR_ASIGNAR,
    motivo_bloqueo: pool.MOTIVO_CUPO_POR_ASIGNAR,
  });
  assert.notEqual(estado, "esperando_pago");
});

test("capacidad pagada agotada no se reporta como 'esperando_pago'", () => {
  const estado = pool.poolEstadoDeEntrada({
    tiene_cupo_activo: false,
    estado_pool: pool.ESTADO_POOL_SIN_CAPACIDAD,
    motivo_bloqueo: pool.MOTIVO_SIN_CAPACIDAD,
  });
  assert.notEqual(estado, "esperando_pago");
});

// ── Safe defaults ────────────────────────────────────────────────────────────

test("payload contradictorio (LISTO sin cupo activo) queda bloqueado", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: pool.ESTADO_POOL_LISTO,
      motivo_bloqueo: null,
    }),
    "bloqueado",
  );
});

test("estado desconocido cae en 'bloqueado'", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: "ESTADO_INVENTADO",
      motivo_bloqueo: "motivo inventado",
    }),
    "bloqueado",
  );
});

test("backend legacy (sin discriminador) usa el motivo de bloqueo", () => {
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: null,
      motivo_bloqueo: pool.MOTIVO_ESPERANDO_PAGO,
    }),
    "esperando_pago",
  );
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: null,
      motivo_bloqueo: pool.MOTIVO_SIN_CAPACIDAD,
    }),
    "sin_capacidad",
  );
  assert.equal(
    pool.poolEstadoDeEntrada({
      tiene_cupo_activo: false,
      estado_pool: null,
      motivo_bloqueo: pool.MOTIVO_CUPO_POR_ASIGNAR,
    }),
    "cupo_por_asignar",
  );
});

// ── Assignment action ────────────────────────────────────────────────────────

test("solo 'listo' puede asignarse", () => {
  const base = { estado_pool: pool.ESTADO_POOL_LISTO, motivo_bloqueo: null };
  assert.equal(
    pool.poolEsAsignable({ ...base, tiene_cupo_activo: true }),
    true,
  );
  for (const estado of [
    pool.ESTADO_POOL_ESPERANDO_PAGO,
    pool.ESTADO_POOL_SIN_CAPACIDAD,
    pool.ESTADO_POOL_CUPO_POR_ASIGNAR,
  ]) {
    assert.equal(
      pool.poolEsAsignable({
        tiene_cupo_activo: false,
        estado_pool: estado,
        motivo_bloqueo: "motivo",
      }),
      false,
    );
  }
});

test("sin equipos destino la accion de asignar se oculta", () => {
  assert.equal(
    pool.poolEsAsignable(
      {
        tiene_cupo_activo: true,
        estado_pool: pool.ESTADO_POOL_LISTO,
        motivo_bloqueo: null,
      },
      true,
    ),
    false,
  );
});
