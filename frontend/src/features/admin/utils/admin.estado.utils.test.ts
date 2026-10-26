/**
 * Focused tests for the state vocabularies of the administration area.
 *
 * The module under test is dependency-free on purpose, so it can be exercised
 * without the React/axios runtime.
 *
 * Run with:
 *   node --experimental-strip-types --test \
 *     src/features/admin/utils/admin.estado.utils.test.ts
 *
 * NOTE: the module is imported through a computed specifier on purpose — Node
 * requires the explicit `.ts` extension to strip the types, while the project
 * `tsconfig` forbids `.ts` extensions in import paths. A computed specifier
 * keeps `tsc --noEmit` clean and still loads the REAL module under test.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

const specifier = "./admin.estado.utils.ts";
const utils = (await import(specifier)) as {
  autorizacionFiestaLabel: (estado: string) => string;
  autorizacionFiestaTone: (estado: string) => string;
  estadoAceptacionLabel: (estado: string) => string;
  estadoAcreditacionLabel: (estado: string) => string;
  estadoAcreditacionTone: (estado: string) => string;
  estadoAsignacionLabel: (estado: string) => string;
  estadoAsignacionTone: (estado: string) => string;
  estadoCompraLabel: (estado: string) => string;
  estadoCompraTone: (estado: string) => string;
  estadoEquipoLabel: (estado: string) => string;
  estadoEquipoTone: (estado: string) => string;
  estadoOrdenLabel: (estado: string) => string;
  estadoOrdenTone: (estado: string) => string;
  estadoParticipacionLabel: (estado: string) => string;
  estadoPersonaLabel: (estado: string) => string;
  estadoPoolLabel: (estado: string) => string;
  estadoPoolTone: (estado: string) => string;
  estadoTransaccionLabel: (estado: string) => string;
  estadoTransaccionTone: (estado: string) => string;
  medioAceptacionLabel: (medio: string) => string;
  resultadoAccesoLabel: (resultado: string) => string;
  resultadoAccesoTone: (resultado: string) => string;
  rosterLabel: (estado: string) => string;
  rosterTone: (estado: string) => string;
  rolParticipanteLabel: (rol: string) => string;
  tipoAceptacionLabel: (tipo: string) => string;
  tipoCompraLabel: (tipo: string) => string;
};

// The states of the REGISTRATION live in the overview module: it is the one
// that renders them. Both modules are leaves, so both can be loaded while
// Node strips the types.
const specifierResumen = "./admin.resumen.utils.ts";
const resumen = (await import(specifierResumen)) as {
  estadoInscripcionLabel: (estado: string) => string;
  estadoInscripcionTone: (estado: string) => string;
};

// ── The inscription states keep the tones of the backend ───────────────────

test("cada estado de inscripcion tiene su tono", () => {
  assert.equal(resumen.estadoInscripcionTone("BORRADOR"), "amber");
  assert.equal(resumen.estadoInscripcionTone("RECIBIDA"), "blue");
  assert.equal(resumen.estadoInscripcionTone("EN_REVISION"), "violet");
  assert.equal(resumen.estadoInscripcionTone("OBSERVADA"), "orange");
  assert.equal(resumen.estadoInscripcionTone("VALIDADA"), "cyan");
  assert.equal(resumen.estadoInscripcionTone("CONFIRMADA"), "emerald");
  assert.equal(resumen.estadoInscripcionTone("RECHAZADA"), "red");
  assert.equal(resumen.estadoInscripcionTone("CANCELADA"), "rose");
});

test("un estado desconocido se muestra de forma neutra y conserva su texto", () => {
  assert.equal(resumen.estadoInscripcionTone("ESTADO_INVENTADO"), "slate");
  assert.equal(
    resumen.estadoInscripcionLabel("ESTADO_INVENTADO"),
    "ESTADO_INVENTADO",
  );
});

// ── The commercial states ───────────────────────────────────────────────────

test("los estados de la compra se distinguen de los de la orden", () => {
  assert.equal(utils.estadoCompraTone("PENDIENTE"), "amber");
  assert.equal(utils.estadoCompraTone("PAGADA"), "emerald");
  assert.equal(utils.estadoCompraTone("CANCELADA"), "rose");
  assert.equal(utils.estadoCompraLabel("PAGADA"), "Pagada");

  assert.equal(utils.estadoOrdenTone("PENDIENTE"), "amber");
  assert.equal(utils.estadoOrdenTone("PAGADA"), "emerald");
  assert.equal(utils.estadoOrdenTone("CANCELADA"), "rose");
  assert.equal(utils.estadoOrdenTone("VENCIDA"), "red");
  assert.equal(utils.estadoOrdenLabel("VENCIDA"), "Vencida");
});

test("el tipo de compra distingue la inicial de la ampliacion", () => {
  assert.equal(utils.tipoCompraLabel("INICIAL"), "Inicial");
  assert.equal(utils.tipoCompraLabel("AMPLIACION"), "Ampliación");
});

// ── The roster, the pool and the assignments ───────────────────────────────

test("la completitud de la plantilla tiene dos tonos", () => {
  assert.equal(utils.rosterTone("COMPLETO"), "emerald");
  assert.equal(utils.rosterTone("INCOMPLETO"), "amber");
  assert.equal(utils.rosterLabel("COMPLETO"), "Completo");
});

test("el estado del pool se distingue del estado de la persona", () => {
  assert.equal(utils.estadoPoolTone("LISTO"), "emerald");
  assert.equal(utils.estadoPoolTone("ESPERANDO_PAGO"), "amber");
  assert.equal(utils.estadoPoolTone("SIN_CAPACIDAD"), "orange");
  assert.equal(utils.estadoPoolTone("CUPO_POR_ASIGNAR"), "blue");
  assert.equal(utils.estadoPoolLabel("LISTO"), "Listo para equipo");

  assert.equal(utils.estadoPersonaLabel("A"), "Activo");
  assert.equal(utils.estadoPersonaLabel("R"), "Retirado");
  assert.equal(utils.estadoParticipacionLabel("A"), "Activa");
  assert.equal(utils.estadoParticipacionLabel("R"), "Retirada");
});

test("el rol del roster distingue jugador, capitan y delegado", () => {
  assert.equal(utils.rolParticipanteLabel("J"), "Jugador");
  assert.equal(utils.rolParticipanteLabel("C"), "Capitán");
  assert.equal(utils.rolParticipanteLabel("D"), "Delegado");
});

test("la asignacion de cupo distingue activa, liberada y revocada", () => {
  assert.equal(utils.estadoAsignacionTone("ACTIVA"), "emerald");
  assert.equal(utils.estadoAsignacionTone("LIBERADA"), "slate");
  assert.equal(utils.estadoAsignacionTone("REVOCADA"), "red");
  assert.equal(utils.estadoAsignacionLabel("ACTIVA"), "Activa");
});

// ── The accreditation and the access log ───────────────────────────────────

test("la acreditacion y la autorizacion de fiesta tienen tonos propios", () => {
  assert.equal(utils.estadoAcreditacionTone("PENDIENTE"), "amber");
  assert.equal(utils.estadoAcreditacionTone("ACTIVA"), "emerald");
  assert.equal(utils.estadoAcreditacionTone("SUSPENDIDA"), "orange");
  assert.equal(utils.estadoAcreditacionTone("REVOCADA"), "red");
  assert.equal(utils.estadoAcreditacionLabel("REVOCADA"), "Revocada");

  assert.equal(utils.autorizacionFiestaTone("AUTOMATICA"), "slate");
  assert.equal(utils.autorizacionFiestaTone("AUTORIZADA"), "emerald");
  assert.equal(utils.autorizacionFiestaTone("BLOQUEADA"), "red");
  assert.equal(utils.autorizacionFiestaLabel("BLOQUEADA"), "Bloqueada");
});

test("el resultado de un acceso distingue permitido de denegado", () => {
  assert.equal(utils.resultadoAccesoTone("PERMITIDO"), "emerald");
  assert.equal(utils.resultadoAccesoTone("DENEGADO"), "red");
  assert.equal(utils.resultadoAccesoLabel("DENEGADO"), "Denegado");
});

test("el intento de pago pendiente no es un cobro", () => {
  assert.equal(utils.estadoTransaccionTone("PENDIENTE"), "amber");
  assert.equal(utils.estadoTransaccionTone("EXITO"), "emerald");
  assert.equal(utils.estadoTransaccionTone("FALLIDO"), "red");
  assert.equal(utils.estadoTransaccionLabel("EXITO"), "Éxito");
});

// ── The legal acceptances and the teams ────────────────────────────────────

test("la aceptacion legal nombra cada tipo", () => {
  assert.equal(utils.tipoAceptacionLabel("BASES"), "Bases del evento");
  assert.equal(utils.tipoAceptacionLabel("APTITUD_FISICA"), "Aptitud física");
  assert.equal(utils.tipoAceptacionLabel("IMAGEN"), "Uso de imagen");
  assert.equal(utils.medioAceptacionLabel("WEB"), "Formulario web");
});

test("el estado del equipo distingue el activo del cancelado", () => {
  assert.equal(utils.estadoEquipoTone("EQUIPO_ACTIVO"), "emerald");
  assert.equal(utils.estadoEquipoTone("EQUIPO_CANCELADO"), "slate");
  assert.equal(utils.estadoEquipoLabel("EQUIPO_ACTIVO"), "Activo");
});
