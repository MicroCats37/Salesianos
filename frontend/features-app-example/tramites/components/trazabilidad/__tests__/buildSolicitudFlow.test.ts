/**
 * Unit tests for buildSolicitudFlow — runnable today with the repo's Node 22
 * via the tsc-compile verification documented in the apply-progress.
 * Zero-dependency: uses node:test + node:assert (built into Node).
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { SolicitudTrazabilidad } from "../../../schemas/trazabilidad.schema";
import {
  buildSolicitudFlow,
  type SolicitudFlow,
  type SolicitudGlobalContext,
} from "../buildSolicitudFlow";

// ── Fixtures ────────────────────────────────────────────────────────────────────

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

// ── Tests ───────────────────────────────────────────────────────────────────────

describe("buildSolicitudFlow", () => {
  it("is deterministic: same input → same output", () => {
    const a = buildSolicitudFlow(trazabilidad, ctx);
    const b = buildSolicitudFlow(trazabilidad, ctx);
    assert.deepEqual(a, b);
  });

  it("produces stable composite ids, never timestamp-only", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    const ids = flow.nodes.map((n) => n.id);
    assert.ok(ids.includes("global-start"));
    assert.ok(ids.includes("global-state-1"));
    assert.ok(ids.includes("global-merge"));
    assert.ok(ids.includes("global-terminal"));
    assert.ok(ids.includes(`area-${A}`));
    assert.ok(ids.includes(`area-${A}-terminal`));
    assert.ok(ids.includes(`area-${A}-period-${P1}`));
    assert.ok(ids.includes(`area-${A}-period-${P1}-terminal`));
    assert.ok(ids.includes(`area-${A}-period-${P1}-participant-${U1}-0`));
    assert.ok(ids.includes(`area-${A}-period-${P1}-participant-${U1}-0-out`));
    assert.ok(ids.includes(`area-${A}-period-${P1}-response-${R1}`));
    assert.ok(ids.includes(`area-${A}-period-${P1}-state-0`));
    for (const id of ids) {
      assert.ok(!/^\d{10,}/.test(id), `id must not be timestamp-only: ${id}`);
    }
  });

  it("orders interleaved events chronologically within a cycle (F04)", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    const order = flow.nodes.filter((n) => n.periodId === P1).map((n) => n.id);
    assert.deepEqual(order, [
      `area-${A}-period-${P1}`,
      `area-${A}-period-${P1}-participant-${U1}-0`,
      `area-${A}-period-${P1}-response-${R1}`,
      `area-${A}-period-${P1}-participant-${U1}-0-out`,
      `area-${A}-period-${P1}-state-0`,
      `area-${A}-period-${P1}-terminal`,
    ]);
  });

  it("every edge resolves to existing nodes with handle-capable endpoints", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    const byId = new Map(flow.nodes.map((n) => [n.id, n]));
    assert.ok(flow.edges.length > 0, "expected at least one edge");
    for (const edge of flow.edges) {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      assert.ok(source, `edge source missing: ${edge.source}`);
      assert.ok(target, `edge target missing: ${edge.target}`);
      assert.equal(
        source.handles.output,
        true,
        `source lacks output: ${edge.source}`,
      );
      assert.equal(
        target.handles.input,
        true,
        `target lacks input: ${edge.target}`,
      );
    }
    // Contract: only the start lacks input, only the terminal lacks output.
    for (const node of flow.nodes) {
      if (node.id === "global-start") {
        assert.equal(node.handles.input, false);
      } else {
        assert.equal(node.handles.input, true, `missing input on ${node.id}`);
      }
      if (node.id === "global-terminal") {
        assert.equal(node.handles.output, false);
      } else {
        assert.equal(node.handles.output, true, `missing output on ${node.id}`);
      }
    }
  });

  it("area branches hang off the chronologically compatible global event", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    const edgeIds = new Set(flow.edges.map((e) => e.id));
    // Area A (10:01) is before EN_GESTION (10:05) → connects from global-start.
    assert.ok(edgeIds.has(`edge-global-start__area-${A}`));
    // Area B (10:10) is after EN_GESTION (10:05) → connects from global-state-1.
    assert.ok(edgeIds.has(`edge-global-state-1__area-${B}`));
  });

  it("converges area branches into a merge node before the terminal", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    assert.equal(flow.mergeNodeId, "global-merge");
    assert.ok(
      flow.edges.some(
        (e) => e.source === `area-${A}-terminal` && e.target === "global-merge",
      ),
    );
    assert.ok(
      flow.edges.some(
        (e) => e.source === `area-${B}-terminal` && e.target === "global-merge",
      ),
    );
    assert.ok(
      flow.edges.some(
        (e) => e.source === "global-merge" && e.target === "global-terminal",
      ),
    );
  });

  it("skips the initial REGISTRADA dupe and labels the terminal by estado", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    assert.ok(!flow.nodes.some((n) => n.id === "global-state-0"));
    const terminal = flow.nodes.find((n) => n.id === "global-terminal");
    assert.equal(terminal?.label, "Finalizada");
    assert.equal(terminal?.timestamp, "2026-09-15T08:00:00.000Z");
  });

  it("creates no participant-removed node when there is no fecha_fin", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    const period2 = flow.nodes.filter((n) => n.periodId === P2);
    assert.ok(period2.some((n) => n.kind === "participant-added"));
    assert.ok(!period2.some((n) => n.kind === "participant-removed"));
    const terminal = flow.nodes.find(
      (n) => n.id === `area-${A}-period-${P2}-terminal`,
    );
    assert.equal(terminal?.open, true);
    assert.equal(terminal?.label, "Ciclo 2 en curso");
  });

  it("builds areaGroups with deterministic node lists", () => {
    const flow = buildSolicitudFlow(trazabilidad, ctx);
    assert.equal(flow.areaGroups.length, 2);
    const groupA = flow.areaGroups.find((g) => g.areaId === A);
    assert.equal(groupA?.areaNombre, "Asesoría Legal");
    assert.equal(groupA?.tipoActual, "PRINCIPAL");
    assert.equal(groupA?.bloqueaCierre, true);
    assert.ok(groupA && groupA.nodeIds[0] === `area-${A}`);
    assert.ok(
      groupA &&
        groupA.nodeIds[groupA.nodeIds.length - 1] === `area-${A}-terminal`,
    );
  });

  it("handles a bare solicitud with no areas and no global history", () => {
    const empty: SolicitudTrazabilidad = {
      solicitud_id: "00000000-0000-4000-8000-000000000000",
      historial_estados: [],
      areas: [],
      timeline: [],
    };
    const flow: SolicitudFlow = buildSolicitudFlow(empty, ctx);
    assert.equal(flow.nodes.length, 2);
    assert.deepEqual(
      flow.nodes.map((n) => n.id),
      ["global-start", "global-terminal"],
    );
    assert.equal(flow.edges.length, 1);
    assert.equal(flow.edges[0].source, "global-start");
    assert.equal(flow.edges[0].target, "global-terminal");
    assert.equal(flow.mergeNodeId, null);
  });
});
