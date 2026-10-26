/**
 * Focused contract test of the Zod mirrors of the administration area.
 *
 * The mirrors are the CLIENT half of the wrapper contract: they must declare
 * EXACTLY the safe fields of the backend wrapper and NEVER a credential, a
 * payment blob or the live QR code
 * (`contract/api-wrapper-presenter-contract.md` §5, §6 and §9).
 *
 * The test reads the SOURCES of the schemas instead of importing them: the
 * schema modules import each other with extensionless specifiers, which Node
 * cannot resolve when it strips the types. Reading the sources keeps the
 * test runnable with the repository pattern:
 *   node --experimental-strip-types --test \
 *     src/features/admin/schemas/admin.esquemas.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

/** Fields that must NEVER be modelled by the administration area. */
const CAMPOS_PROHIBIDOS = [
  "password",
  "password_hash",
  "token",
  "token_sesion",
  "codigo_qr",
  "metadata",
  "transaction_id",
  "response_message",
  "is_superuser",
];

const ESQUEMAS = [
  "admin.inscripcion.schema.ts",
  "admin.pago.schema.ts",
  "admin.acreditacion.schema.ts",
  "admin.usuario.schema.ts",
  "admin.catalogos.schema.ts",
  "admin.resumen.schema.ts",
  "admin.me.schema.ts",
];

function leerEsquema(nombre: string): string {
  return readFileSync(new URL(nombre, import.meta.url), "utf8");
}

// ── No forbidden field is ever declared ────────────────────────────────────

test("ningun esquema declara un campo prohibido", () => {
  for (const nombre of ESQUEMAS) {
    const fuente = leerEsquema(nombre);

    for (const campo of CAMPOS_PROHIBIDOS) {
      const declarado = new RegExp(`^\\s*${campo}\\s*:`, "m").test(fuente);

      assert.equal(
        declarado,
        false,
        `${nombre} declara el campo prohibido "${campo}"`,
      );
    }
  }
});

test("la fuente de los esquemas prohibidos no se puede esquivar", () => {
  // El contrato se cumple sobre la DECLARACION de los campos, no sobre las
  // menciones de los documentos: los comentarios que explican por que un
  // campo NO existe son correctos y obligatorios.
  const fuente = leerEsquema("admin.pago.schema.ts");

  assert.ok(fuente.includes("token_sesion"));
  assert.equal(/^\s*token_sesion\s*:/m.test(fuente), false);
});

// ── The pagination container mirrors `core.pagination.PaginatedData` ───────

test("el contenedor paginado declara los cinco campos del backend", () => {
  const fuente = leerEsquema("admin.paginacion.schema.ts");

  for (const campo of ["items", "total", "page", "page_size", "total_pages"]) {
    assert.ok(
      new RegExp(`^\\s*${campo}\\s*:`, "m").test(fuente),
      `el contenedor paginado no declara "${campo}"`,
    );
  }
});

// ── The mirrors are composed, not duplicated ───────────────────────────────

test("el detalle de una inscripcion hereda el listado y anade los seis bloques", () => {
  const fuente = leerEsquema("admin.inscripcion.schema.ts");

  assert.ok(
    fuente.includes("AdminInscripcionListItemSchema.extend"),
    "el detalle de la inscripcion no hereda el wrapper del listado",
  );

  for (const bloque of [
    "equipos",
    "participantes",
    "compras",
    "asignaciones",
    "aceptaciones",
    "saldo",
  ]) {
    assert.ok(
      new RegExp(`^\\s*${bloque}\\s*:`, "m").test(fuente),
      `el detalle de la inscripcion no declara el bloque "${bloque}"`,
    );
  }
});

test("el detalle de un pago hereda el listado y anade los intentos", () => {
  const fuente = leerEsquema("admin.pago.schema.ts");

  assert.ok(fuente.includes("AdminPagoListItemSchema.extend"));
  assert.ok(/^\s*transacciones\s*:/m.test(fuente));
});

test("el detalle de una acreditacion hereda el listado y anade los accesos", () => {
  const fuente = leerEsquema("admin.acreditacion.schema.ts");

  assert.ok(fuente.includes("AdminAcreditacionListItemSchema.extend"));
  assert.ok(/^\s*accesos\s*:/m.test(fuente));
});

test("el detalle de un usuario hereda el listado y anade las inscripciones", () => {
  const fuente = leerEsquema("admin.usuario.schema.ts");

  assert.ok(fuente.includes("AdminUsuarioListItemSchema.extend"));
  assert.ok(/^\s*personas\s*:/m.test(fuente));
});
