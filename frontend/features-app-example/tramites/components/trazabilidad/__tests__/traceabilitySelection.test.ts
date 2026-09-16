/**
 * Unit tests for traceabilitySelection — the single stable-ID selection model
 * (audit G, U7). Zero-dependency: node:test + node:assert via the repo's tsx.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { SolicitudTrazabilidad } from "../../../schemas/trazabilidad.schema";
import type { SolicitudGlobalContext } from "../buildSolicitudFlow";
import {
  globalStateEntryForNodeId,
  globalStateNodeIdForTimestamp,
  parseFlowNodeId,
  resolveSelection,
  toFlowSelection,
} from "../traceabilitySelection";

// ── Fixtures (mirror buildSolicitudFlow.test.ts) ───────────────────────────────

const A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const P1 = "11111111-1111-4111-8111-111111111111";
const P2 = "22222222-2222-4222-8222-222222222222";
const P3 = "33333333-3333-4333-8333-333333333333";
const U1 = "11111111-2222-4333-8444-555555555555";
const U2 = "66666666-7777-4888-8999-000000000000";
const R1 = "aaaa1111-bbbb-4ccc-8ddd-eeeeeeeeeeee";

const ctx: SolicitudGlobalContext = {
  fecha_registro: "2026-09-01T10:00:00.000Z",
  estado: "FINALIZADA",
  fecha_cierre: "2026-09-15T08:00:00.000Z",
  id_publico: "LIMA-2026-0003",
};

const trazabilidad: SolicitudTrazabilidad = {
  solicitud_id: "00000000-0000-4000-8000-000000000000",
  historial_estados: [
    {
      estado_anterior: null,
      estado_nuevo: "REGISTRADA",
      fecha_cambio: "2026-09-01T10:00:00.000Z",
      cambiado_por_id: "00000000-0000-4000-8000-000000000000",
      cambiado_por_nombres: "Sistema",
      origen: "CREACION",
      observacion: null,
    },
    {
      estado_anterior: "REGISTRADA",
      estado_nuevo: "EN_GESTION",
      fecha_cambio: "2026-09-01T10:05:00.000Z",
      cambiado_por_id: "00000000-0000-4000-8000-000000000000",
      cambiado_por_nombres: "Ana Pérez",
      origen: "ASIGNACION",
      observacion: null,
    },
  ],
  areas: [
    {
      id: A,
      area_id: A,
      area_nombre: "Asesoría Legal",
      bloquea_cierre: true,
      fecha_incorporacion: "2026-09-01T10:01:00.000Z",
      incorporado_por_id: "00000000-0000-4000-8000-000000000000",
      incorporado_por_nombres: "Ana Pérez",
      observacion: null,
      tipo_actual: "PRINCIPAL",
      etapas: [
        {
          id: P1,
          numero_ciclo: 1,
          tipo_participacion: "PRINCIPAL",
          estado: "CERRADO",
          fecha_inicio: "2026-09-01T10:02:00.000Z",
          fecha_fin: "2026-09-01T10:08:00.000Z",
          tipo_cierre: "FINALIZADO",
          iniciado_por_id: "00000000-0000-4000-8000-000000000000",
          iniciado_por_nombres: "Ana Pérez",
          finalizado_por_id: "00000000-0000-4000-8000-000000000000",
          finalizado_por_nombres: "Ana Pérez",
          motivo_cierre: null,
          historial_estados: [
            {
              estado_anterior: "PENDIENTE",
              estado_nuevo: "EN_GESTION",
              fecha_cambio: "2026-09-01T10:07:00.000Z",
              cambiado_por_id: "00000000-0000-4000-8000-000000000000",
              cambiado_por_nombres: "Ana Pérez",
              origen: "AUTOASIGNACION",
              motivo: null,
            },
          ],
          participantes: [
            {
              usuario_id: U1,
              usuario_nombres: "Carlos Ruiz",
              rol: "Abogado",
              fecha_inicio: "2026-09-01T10:03:00.000Z",
              fecha_fin: "2026-09-01T10:06:00.000Z",
              activo: false,
              asignado_por_id: "00000000-0000-4000-8000-000000000000",
              asignado_por_nombres: "Ana Pérez",
              retirado_por_id: "00000000-0000-4000-8000-000000000000",
              retirado_por_nombres: "Ana Pérez",
              motivo_retiro: "Tarea completa",
            },
          ],
          respuestas: [
            {
              id: R1,
              tipo_respuesta: "CONFORMIDAD",
              contenido: null,
              estado: "EMITIDA",
              fecha_emision: "2026-09-01T10:04:00.000Z",
              emitido_por_id: "00000000-0000-4000-8000-000000000000",
              emitido_por_nombres: "Carlos Ruiz",
            },
          ],
        },
        {
          id: P2,
          numero_ciclo: 2,
          tipo_participacion: "PRINCIPAL",
          estado: "EN_GESTION",
          fecha_inicio: "2026-09-01T10:09:00.000Z",
          fecha_fin: null,
          tipo_cierre: null,
          iniciado_por_id: "00000000-0000-4000-8000-000000000000",
          iniciado_por_nombres: "Ana Pérez",
          finalizado_por_id: null,
          finalizado_por_nombres: null,
          motivo_cierre: null,
          historial_estados: [],
          participantes: [
            {
              usuario_id: U2,
              usuario_nombres: "Luis Torres",
              rol: "Analista",
              fecha_inicio: "2026-09-01T10:09:30.000Z",
              fecha_fin: null,
              activo: true,
              asignado_por_id: "00000000-0000-4000-8000-000000000000",
              asignado_por_nombres: "Ana Pérez",
              retirado_por_id: null,
              retirado_por_nombres: null,
              motivo_retiro: null,
            },
          ],
          respuestas: [],
        },
      ],
    },
    {
      id: B,
      area_id: B,
      area_nombre: "Centro Médico",
      bloquea_cierre: false,
      fecha_incorporacion: "2026-09-01T10:10:00.000Z",
      incorporado_por_id: "00000000-0000-4000-8000-000000000000",
      incorporado_por_nombres: "Ana Pérez",
      observacion: null,
      tipo_actual: "ADJUNTA",
      etapas: [
        {
          id: P3,
          numero_ciclo: 1,
          tipo_participacion: "ADJUNTA",
          estado: "CERRADO",
          fecha_inicio: "2026-09-01T10:11:00.000Z",
          fecha_fin: "2026-09-01T10:12:00.000Z",
          tipo_cierre: "ASIGNACION_ERRONEA",
          iniciado_por_id: "00000000-0000-4000-8000-000000000000",
          iniciado_por_nombres: "Ana Pérez",
          finalizado_por_id: "00000000-0000-4000-8000-000000000000",
          finalizado_por_nombres: "Ana Pérez",
          motivo_cierre: "Área no correspondía",
          historial_estados: [],
          participantes: [],
          respuestas: [],
        },
      ],
    },
  ],
  timeline: [],
};

// ── parseFlowNodeId ────────────────────────────────────────────────────────────

describe("parseFlowNodeId", () => {
  it("decodes the global nodes", () => {
    assert.deepEqual(parseFlowNodeId("global-start"), {
      kind: "global",
      nodeId: "global-start",
    });
    assert.deepEqual(parseFlowNodeId("global-merge"), {
      kind: "global",
      nodeId: "global-merge",
    });
    assert.deepEqual(parseFlowNodeId("global-terminal"), {
      kind: "global",
      nodeId: "global-terminal",
    });
  });

  it("decodes global-state indices", () => {
    assert.deepEqual(parseFlowNodeId("global-state-1"), {
      kind: "global-state",
      globalStateIndex: 1,
    });
  });

  it("decodes area, period, participant, response and state ids (dash UUIDs)", () => {
    assert.deepEqual(parseFlowNodeId(`area-${A}`), {
      kind: "area",
      areaId: A,
    });
    assert.deepEqual(parseFlowNodeId(`area-${A}-terminal`), {
      kind: "area-terminal",
      areaId: A,
    });
    assert.deepEqual(parseFlowNodeId(`area-${A}-period-${P1}`), {
      kind: "period",
      areaId: A,
      periodId: P1,
    });
    assert.deepEqual(parseFlowNodeId(`area-${A}-period-${P1}-terminal`), {
      kind: "period-terminal",
      areaId: A,
      periodId: P1,
    });
    assert.deepEqual(
      parseFlowNodeId(`area-${A}-period-${P1}-participant-${U1}-0`),
      {
        kind: "participant",
        areaId: A,
        periodId: P1,
        participantUserId: U1,
      },
    );
    assert.deepEqual(
      parseFlowNodeId(`area-${A}-period-${P1}-participant-${U1}-0-out`),
      {
        kind: "participant",
        areaId: A,
        periodId: P1,
        participantUserId: U1,
      },
    );
    assert.deepEqual(parseFlowNodeId(`area-${A}-period-${P1}-response-${R1}`), {
      kind: "response",
      areaId: A,
      periodId: P1,
      responseId: R1,
    });
    assert.deepEqual(parseFlowNodeId(`area-${A}-period-${P1}-state-0`), {
      kind: "state",
      areaId: A,
      periodId: P1,
    });
  });

  it("returns null for unknown ids", () => {
    assert.equal(parseFlowNodeId("area-group-abc"), null);
    assert.equal(parseFlowNodeId("unknown"), null);
    assert.equal(parseFlowNodeId("area-123-not-a-uuid"), null);
  });
});

// ── Global-state ↔ flow node mirror ────────────────────────────────────────────

describe("global-state ↔ flow node mirror", () => {
  const registro = ctx.fecha_registro;

  it("maps a real transition timestamp to its node id (skipping REGISTRADA dupe)", () => {
    assert.equal(
      globalStateNodeIdForTimestamp(
        trazabilidad.historial_estados,
        registro,
        Date.parse("2026-09-01T10:05:00.000Z"),
      ),
      "global-state-1",
    );
  });

  it("returns null for the skipped initial REGISTRADA dupe", () => {
    assert.equal(
      globalStateNodeIdForTimestamp(
        trazabilidad.historial_estados,
        registro,
        Date.parse("2026-09-01T10:00:00.000Z"),
      ),
      null,
    );
  });

  it("resolves a node id back to its historial entry", () => {
    const entry = globalStateEntryForNodeId(
      trazabilidad.historial_estados,
      registro,
      "global-state-1",
    );
    assert.ok(entry);
    assert.equal(entry.estado_nuevo, "EN_GESTION");
    assert.equal(
      globalStateEntryForNodeId(
        trazabilidad.historial_estados,
        registro,
        "global-state-0",
      ),
      null,
    );
  });
});

// ── toFlowSelection ───────────────────────────────────────────────────────────

describe("toFlowSelection", () => {
  it("maps period and area selections directly", () => {
    assert.deepEqual(
      toFlowSelection(
        { type: "period", areaId: A, periodId: P1 },
        trazabilidad,
        ctx,
      ),
      { type: "period", areaId: A, periodId: P1 },
    );
    assert.deepEqual(
      toFlowSelection({ type: "area", areaId: B }, trazabilidad, ctx),
      { type: "area", areaId: B },
    );
  });

  it("maps node selections verbatim", () => {
    assert.deepEqual(
      toFlowSelection(
        { type: "node", nodeId: "global-start" },
        trazabilidad,
        ctx,
      ),
      { type: "node", nodeId: "global-start" },
    );
  });

  it("maps response selection to its deterministic node id", () => {
    assert.deepEqual(
      toFlowSelection(
        { type: "response", areaId: A, periodId: P1, responseId: R1 },
        trazabilidad,
        ctx,
      ),
      { type: "node", nodeId: `area-${A}-period-${P1}-response-${R1}` },
    );
  });

  it("maps participant-event to the participant node, falling back to period", () => {
    assert.deepEqual(
      toFlowSelection(
        {
          type: "participant-event",
          areaId: A,
          periodId: P1,
          participantUserId: U1,
        },
        trazabilidad,
        ctx,
      ),
      { type: "node", nodeId: `area-${A}-period-${P1}-participant-${U1}-0` },
    );
    assert.deepEqual(
      toFlowSelection(
        {
          type: "participant-event",
          areaId: A,
          periodId: P1,
          participantUserId: "00000000-0000-4000-8000-000000000099",
        },
        trazabilidad,
        ctx,
      ),
      { type: "period", areaId: A, periodId: P1 },
    );
  });

  it("maps a global-state selection to its node, null for the skipped dupe", () => {
    assert.deepEqual(
      toFlowSelection(
        { type: "global-state", stateId: "2026-09-01T10:05:00.000Z" },
        trazabilidad,
        ctx,
      ),
      { type: "node", nodeId: "global-state-1" },
    );
    assert.equal(
      toFlowSelection(
        { type: "global-state", stateId: "2026-09-01T10:00:00.000Z" },
        trazabilidad,
        ctx,
      ),
      null,
    );
  });
});

// ── resolveSelection ───────────────────────────────────────────────────────────

describe("resolveSelection", () => {
  it("resolves period, area, participant and response selections", () => {
    const period = resolveSelection(
      { type: "period", areaId: A, periodId: P1 },
      trazabilidad,
      ctx,
    );
    assert.ok(period && period.type === "period");
    assert.equal(period.period.id, P1);
    assert.equal(period.area.id, A);

    const area = resolveSelection(
      { type: "area", areaId: B },
      trazabilidad,
      ctx,
    );
    assert.ok(area && area.type === "area");
    assert.equal(area.area.id, B);

    const participant = resolveSelection(
      {
        type: "participant-event",
        areaId: A,
        periodId: P1,
        participantUserId: U1,
      },
      trazabilidad,
      ctx,
    );
    assert.ok(participant && participant.type === "participant-event");
    assert.equal(participant.participant.usuario_id, U1);

    const response = resolveSelection(
      { type: "response", areaId: A, periodId: P1, responseId: R1 },
      trazabilidad,
      ctx,
    );
    assert.ok(response && response.type === "response");
    assert.equal(response.response.id, R1);
  });

  it("resolves a global-state selection to its historial entry", () => {
    const sel = resolveSelection(
      { type: "global-state", stateId: "2026-09-01T10:05:00.000Z" },
      trazabilidad,
      ctx,
    );
    assert.ok(sel && sel.type === "global-state");
    assert.equal(sel.historial.estado_nuevo, "EN_GESTION");
  });

  it("resolves node ids back to entities (bidirectional sync)", () => {
    const fromResponse = resolveSelection(
      { type: "node", nodeId: `area-${A}-period-${P1}-response-${R1}` },
      trazabilidad,
      ctx,
    );
    assert.ok(fromResponse && fromResponse.type === "response");
    assert.equal(fromResponse.response.id, R1);

    const fromParticipantOut = resolveSelection(
      {
        type: "node",
        nodeId: `area-${A}-period-${P1}-participant-${U1}-0-out`,
      },
      trazabilidad,
      ctx,
    );
    assert.ok(
      fromParticipantOut && fromParticipantOut.type === "participant-event",
    );
    assert.equal(fromParticipantOut.participant.usuario_id, U1);

    const fromStateNode = resolveSelection(
      { type: "node", nodeId: `area-${A}-period-${P1}-state-0` },
      trazabilidad,
      ctx,
    );
    assert.ok(fromStateNode && fromStateNode.type === "period");
    assert.equal(fromStateNode.period.id, P1);

    const fromAreaTerminal = resolveSelection(
      { type: "node", nodeId: `area-${A}-terminal` },
      trazabilidad,
      ctx,
    );
    assert.ok(fromAreaTerminal && fromAreaTerminal.type === "area");
    assert.equal(fromAreaTerminal.area.id, A);

    const fromGlobalState = resolveSelection(
      { type: "node", nodeId: "global-state-1" },
      trazabilidad,
      ctx,
    );
    assert.ok(fromGlobalState && fromGlobalState.type === "global-state");
    assert.equal(fromGlobalState.historial.estado_nuevo, "EN_GESTION");
  });

  it("resolves global nodes to compact node summaries", () => {
    const start = resolveSelection(
      { type: "node", nodeId: "global-start" },
      trazabilidad,
      ctx,
    );
    assert.ok(start && start.type === "node");
    assert.equal(start.kind, "global-start");
    assert.equal(start.label, "Solicitud registrada");

    const terminal = resolveSelection(
      { type: "node", nodeId: "global-terminal" },
      trazabilidad,
      ctx,
    );
    assert.ok(terminal && terminal.type === "node");
    assert.equal(terminal.kind, "global-terminal");
    assert.equal(terminal.label, "Finalizada");

    const merge = resolveSelection(
      { type: "node", nodeId: "global-merge" },
      trazabilidad,
      ctx,
    );
    assert.ok(merge && merge.type === "node");
    assert.equal(merge.kind, "global-merge");
    assert.equal(merge.label, "Convergencia");
  });

  it("returns null for unresolvable selections", () => {
    assert.equal(resolveSelection(null, trazabilidad, ctx), null);
    assert.equal(
      resolveSelection(
        {
          type: "period",
          areaId: A,
          periodId: "00000000-0000-4000-8000-000000000099",
        },
        trazabilidad,
        ctx,
      ),
      null,
    );
    assert.equal(
      resolveSelection(
        { type: "global-state", stateId: "2026-09-01T99:99:00.000Z" },
        trazabilidad,
        ctx,
      ),
      null,
    );
  });
});
