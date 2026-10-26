/**
 * Focused tests for the ORDERING whitelists of the administration area.
 *
 * The whitelists are the client mirror of the backend `ORDERING_*` maps of
 * `AdminOperacionService`. The backend rejects an unknown field with 422
 * `INVALID_REQUEST`, so a field offered by the UI that the backend does NOT
 * accept is a broken control, not a cosmetic detail: this test pins the
 * mirror against the documented contract.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/admin/utils/admin.orden.utils.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./admin.orden.utils.ts";
const orden = (await import(specifier)) as {
  ORDEN_INSCRIPCIONES: { campo: string }[];
  ORDEN_PAGOS: { campo: string }[];
  ORDEN_EQUIPOS: { campo: string }[];
  ORDEN_PARTICIPANTES: { campo: string }[];
  ORDEN_PARTICIPACIONES: { campo: string }[];
  ORDEN_ACREDITACIONES: { campo: string }[];
  ORDEN_ACCESOS: { campo: string }[];
  ORDEN_USUARIOS: { campo: string }[];
  ORDEN_POR_DEFECTO_INSCRIPCIONES: string;
  ORDEN_POR_DEFECTO_PAGOS: string;
  ORDEN_POR_DEFECTO_EQUIPOS: string;
  ORDEN_POR_DEFECTO_PARTICIPANTES: string;
  ORDEN_POR_DEFECTO_PARTICIPACIONES: string;
  ORDEN_POR_DEFECTO_ACREDITACIONES: string;
  ORDEN_POR_DEFECTO_ACCESOS: string;
  ORDEN_POR_DEFECTO_USUARIOS: string;
};

const listaSpecifier = "./admin.lista.utils.ts";
const lista = (await import(listaSpecifier)) as {
  adminEsOrdenValido: (ordering: string, permitidos: string[]) => boolean;
  adminOpcionesOrdering: (campos: { campo: string }[]) => {
    valor: string;
    etiqueta: string;
  }[];
};

/** The documented contract — the SAME public fields the backend accepts. */
const CONTRATO: Record<string, string[]> = {
  A3: ["created_at", "estado", "responsable", "paquete"],
  A5: [
    "created_at",
    "total",
    "cantidad",
    "estado_compra",
    "estado_orden",
    "pagada_en",
  ],
  A7: ["created_at", "nombre", "disciplina", "estado"],
  A8: ["created_at", "persona", "estado"],
  A9: ["created_at", "persona", "equipo", "disciplina", "rol", "estado"],
  A10: ["persona", "estado", "autorizacion_fiesta"],
  A12: ["fecha_hora", "resultado", "punto_acceso"],
  A13: ["created_at", "username", "nombres", "last_login"],
};

const LISTAS: Record<string, { campo: string }[]> = {
  A3: orden.ORDEN_INSCRIPCIONES,
  A5: orden.ORDEN_PAGOS,
  A7: orden.ORDEN_EQUIPOS,
  A8: orden.ORDEN_PARTICIPANTES,
  A9: orden.ORDEN_PARTICIPACIONES,
  A10: orden.ORDEN_ACREDITACIONES,
  A12: orden.ORDEN_ACCESOS,
  A13: orden.ORDEN_USUARIOS,
};

test("cada lista ofrece exactamente los campos del contrato", () => {
  for (const [superficie, campos] of Object.entries(LISTAS)) {
    assert.deepEqual(
      campos.map((campo) => campo.campo),
      CONTRATO[superficie],
      `la lista ${superficie} no coincide con el contrato`,
    );
  }
});

test("ninguna lista ofrece un campo repetido", () => {
  for (const [superficie, campos] of Object.entries(LISTAS)) {
    const nombres = campos.map((campo) => campo.campo);
    assert.equal(
      new Set(nombres).size,
      nombres.length,
      `la lista ${superficie} ofrece un campo repetido`,
    );
  }
});

test("el backend aceptaria todos los campos ofrecidos por el cliente", () => {
  for (const [superficie, campos] of Object.entries(LISTAS)) {
    const permitidos = campos.map((campo) => campo.campo);
    for (const campo of permitidos) {
      assert.equal(
        lista.adminEsOrdenValido(campo, permitidos),
        true,
        `${superficie}.${campo} es rechazado por la lista blanca`,
      );
      assert.equal(
        lista.adminEsOrdenValido(`-${campo}`, permitidos),
        true,
        `${superficie}.-${campo} es rechazado por la lista blanca`,
      );
    }
    assert.equal(
      lista.adminEsOrdenValido("campo_inexistente", permitidos),
      false,
      `${superficie} acepta un campo fuera del contrato`,
    );
  }
});

test("cada campo produce las dos direcciones de ordenamiento", () => {
  for (const [superficie, campos] of Object.entries(LISTAS)) {
    const opciones = lista.adminOpcionesOrdering(campos);
    assert.equal(
      opciones.length,
      campos.length * 2,
      `la lista ${superficie} no ofrece las dos direcciones`,
    );
    for (const campo of campos) {
      assert.ok(opciones.some((opcion) => opcion.valor === campo.campo));
      assert.ok(opciones.some((opcion) => opcion.valor === `-${campo.campo}`));
    }
  }
});

test("los ordenes por defecto coinciden con el contrato", () => {
  assert.equal(orden.ORDEN_POR_DEFECTO_INSCRIPCIONES, "-created_at");
  assert.equal(orden.ORDEN_POR_DEFECTO_PAGOS, "-created_at");
  assert.equal(orden.ORDEN_POR_DEFECTO_EQUIPOS, "-created_at");
  assert.equal(orden.ORDEN_POR_DEFECTO_PARTICIPANTES, "-created_at");
  assert.equal(orden.ORDEN_POR_DEFECTO_PARTICIPACIONES, "-created_at");
  assert.equal(orden.ORDEN_POR_DEFECTO_ACREDITACIONES, "persona");
  assert.equal(orden.ORDEN_POR_DEFECTO_ACCESOS, "-fecha_hora");
  assert.equal(orden.ORDEN_POR_DEFECTO_USUARIOS, "-created_at");
});
