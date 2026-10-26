/**
 * Focused tests for the mapping of the operational overview.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/admin/utils/admin.resumen.utils.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./admin.resumen.utils.ts";
const utils = (await import(specifier)) as {
  estadoInscripcionTone: (estado: string) => string;
  estadoInscripcionLabel: (estado: string) => string;
  formatearFecha: (fecha: string | null | undefined) => string;
  formatearMonto: (monto: number) => string;
  formatearNumero: (valor: number) => string;
  resumenKpis: (resumen: unknown) => Array<{
    id: string;
    label: string;
    value: string;
    rawValue: number;
    hint: string;
    tone: string;
  }>;
  resumenAlertas: (resumen: unknown) => Array<{
    id: string;
    title: string;
    items: Array<{ id: string; value: number }>;
  }>;
};

const resumen = {
  evento: {
    id: "evt-1",
    nombre: "Salesianos FEST 2026",
    fecha_inicio: "2026-10-01",
    fecha_fin: "2026-11-21",
    esta_activo: true,
    fecha_limite_modificacion: "2026-11-01",
    puede_modificar: true,
  },
  inscripciones: {
    total: 12,
    por_estado: {
      BORRADOR: 1,
      RECIBIDA: 2,
      EN_REVISION: 3,
      OBSERVADA: 0,
      VALIDADA: 1,
      CONFIRMADA: 4,
      RECHAZADA: 0,
      CANCELADA: 1,
    },
    creadas_ultimos_7_dias: 2,
  },
  pagos: {
    compras_total: 9,
    compras_pagadas: 5,
    compras_pendientes: 3,
    compras_canceladas: 1,
    monto_pagado: 1234.5,
    monto_pendiente: 300,
    ordenes_vencidas: 1,
    compras_pagadas_sin_liquidar: 2,
  },
  cupos: {
    contratado: 40,
    pagado: 30,
    asignado_activo: 20,
    disponible_pagado: 10,
    inscripciones_con_capacidad_exhaustada: 1,
  },
  equipos: {
    total: 8,
    completos: 5,
    incompletos: 3,
    por_disciplina: [],
  },
  participantes: {
    personas_distintas: 25,
    participaciones_activas: 30,
    en_pool: 4,
    sin_cupo_activo: 6,
  },
  acreditaciones: {
    total: 25,
    por_estado: { PENDIENTE: 5, ACTIVA: 18, SUSPENDIDA: 1, REVOCADA: 1 },
    con_acceso_fiesta: 20,
    bloqueadas_por_admin: 2,
  },
  accesos: {
    permitidos: 40,
    denegados: 3,
    ultimo_acceso: "2026-10-25T10:00:00",
  },
};

// ── The tiles render what the backend computed — they never recompute ────────

test("el resumen expone los siete tiles de los bloques metricos", () => {
  const kpis = utils.resumenKpis(resumen);
  assert.equal(kpis.length, 7);
  assert.deepEqual(
    kpis.map((kpi) => kpi.id),
    [
      "inscripciones",
      "pagos",
      "cupos",
      "equipos",
      "participantes",
      "acreditaciones",
      "accesos",
    ],
  );
});

test("el tile de pagos muestra el monto pagado del backend", () => {
  const pagos = utils.resumenKpis(resumen).find((kpi) => kpi.id === "pagos");
  assert.ok(pagos);
  assert.equal(pagos.rawValue, 1234.5);
});

test("el tile de cupos NO deriva saldos", () => {
  const cupos = utils.resumenKpis(resumen).find((kpi) => kpi.id === "cupos");
  assert.ok(cupos);
  // `pagado` (30) es el dato del backend. El disponible (10) es otro bloque.
  assert.equal(cupos.rawValue, 30);
});

test("el tile de participantes usa las personas, no las participaciones", () => {
  const participantes = utils
    .resumenKpis(resumen)
    .find((kpi) => kpi.id === "participantes");
  assert.ok(participantes);
  assert.equal(participantes.rawValue, 25);
});

// ── The attention lists only report real pending work ───────────────────────

test("las cuatro listas de atencion se construyen desde el resumen", () => {
  const alertas = utils.resumenAlertas(resumen);
  assert.deepEqual(
    alertas.map((grupo) => grupo.id),
    ["inscripciones", "pagos", "cupos", "equipos"],
  );
});

test("un estado con cero.no aparece como alerta", () => {
  const alertas = utils.resumenAlertas(resumen);
  const inscripciones = alertas.find((grupo) => grupo.id === "inscripciones");
  assert.ok(inscripciones);
  assert.equal(inscripciones.items.length, 2);
  assert.deepEqual(
    inscripciones.items.map((item) => item.id),
    ["inscripcion-RECIBIDA", "inscripcion-EN_REVISION"],
  );
});

test("un area sin pendientes no genera una lista vacia", () => {
  const sinPendientes = {
    ...resumen,
    inscripciones: { ...resumen.inscripciones, por_estado: {} },
    pagos: {
      ...resumen.pagos,
      compras_pendientes: 0,
      ordenes_vencidas: 0,
      compras_pagadas_sin_liquidar: 0,
    },
    cupos: {
      ...resumen.cupos,
      disponible_pagado: 0,
      inscripciones_con_capacidad_exhaustada: 0,
    },
    participantes: { ...resumen.participantes, sin_cupo_activo: 0, en_pool: 0 },
    equipos: { ...resumen.equipos, incompletos: 0 },
  };

  assert.deepEqual(utils.resumenAlertas(sinPendientes), []);
});

// ── The state vocabulary keeps the tones of the backend ─────────────────────

test("cada estado de inscripcion tiene su tono", () => {
  assert.equal(utils.estadoInscripcionTone("BORRADOR"), "amber");
  assert.equal(utils.estadoInscripcionTone("RECIBIDA"), "blue");
  assert.equal(utils.estadoInscripcionTone("EN_REVISION"), "violet");
  assert.equal(utils.estadoInscripcionTone("OBSERVADA"), "orange");
  assert.equal(utils.estadoInscripcionTone("VALIDADA"), "cyan");
  assert.equal(utils.estadoInscripcionTone("CONFIRMADA"), "emerald");
  assert.equal(utils.estadoInscripcionTone("RECHAZADA"), "red");
  assert.equal(utils.estadoInscripcionTone("CANCELADA"), "rose");
});

test("un estado desconocido se muestra de forma neutra", () => {
  assert.equal(utils.estadoInscripcionTone("ESTADO_INVENTADO"), "slate");
  assert.equal(
    utils.estadoInscripcionLabel("ESTADO_INVENTADO"),
    "ESTADO_INVENTADO",
  );
});

// ── The formatters never shift the date by time zone ───────────────────────

test("una fecha sin hora se formatea sin desfase de zona horaria", () => {
  assert.equal(utils.formatearFecha("2026-10-25"), "25/10/2026");
});

test("una fecha ausente se muestra como guion", () => {
  assert.equal(utils.formatearFecha(null), "—");
  assert.equal(utils.formatearFecha(undefined), "—");
});

test("los montos conservan los centavos", () => {
  assert.equal(utils.formatearMonto(1234.5).replace(/\D/g, ""), "123450");
});

test("los numeros conservan sus digitos", () => {
  assert.equal(utils.formatearNumero(1234).replace(/\D/g, ""), "1234");
});
