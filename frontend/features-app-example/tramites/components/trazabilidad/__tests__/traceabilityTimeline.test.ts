/**
 * Unit tests for traceabilityTimeline — runnable today with the repo's Node 22
 * via the tsc-compile verification documented in the apply-progress.
 * Zero-dependency: uses node:test + node:assert (built into Node).
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { AsignacionTrazabilidad } from "../../../schemas/trazabilidad.schema";
import {
  buildGlobalStateSegments,
  buildLifecycleBounds,
  clampVisibleRange,
  formatDuration,
  formatTimelineDate,
  type LifecycleInput,
  PAD_FLOOR_MS,
} from "../traceabilityTimeline";

const T = (iso: string): number => Date.parse(iso);
const ISO = "2026-09-01T10:00:00.000Z";
const DAY_MS = 86_400_000;

function emptyArea(): AsignacionTrazabilidad {
  return {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    area_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    area_nombre: "Asesoría Legal",
    bloquea_cierre: false,
    fecha_incorporacion: "2026-09-01T10:01:00.000Z",
    incorporado_por_id: "00000000-0000-4000-8000-000000000000",
    incorporado_por_nombres: "Ana Pérez",
    observacion: null,
    tipo_actual: "PRINCIPAL",
    etapas: [],
  };
}

const CLOSED_HISTORIAL = [
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
  {
    estado_anterior: "EN_GESTION",
    estado_nuevo: "FINALIZADA",
    fecha_cambio: "2026-09-01T10:20:00.000Z",
    cambiado_por_id: "00000000-0000-4000-8000-000000000000",
    cambiado_por_nombres: "Ana Pérez",
    origen: "RESPUESTA_FINAL",
    observacion: null,
  },
];

describe("buildLifecycleBounds", () => {
  it("closed trámite ends at the last real event / fecha_cierre, never now (F08)", () => {
    const input: LifecycleInput = {
      historial_estados: CLOSED_HISTORIAL,
      areas: [emptyArea()],
      timeline: [],
      fecha_registro: "2026-09-01T10:00:00.000Z",
      fecha_cierre: "2026-09-01T10:20:00.000Z",
      estado: "FINALIZADA",
      now: T("2026-09-10T12:00:00.000Z"),
    };
    const bounds = buildLifecycleBounds(input);
    assert.equal(bounds.hasOpenPeriod, false);
    assert.equal(bounds.dataStart, T("2026-09-01T10:00:00.000Z"));
    assert.equal(bounds.dataEnd, T("2026-09-01T10:20:00.000Z"));
    assert.ok(
      bounds.maxBound !== null && bounds.maxBound < bounds.now,
      "closed trámite must not extend to now",
    );
  });

  it("open period includes now in the data range", () => {
    const area = emptyArea();
    area.etapas = [
      {
        id: "11111111-1111-4111-8111-111111111111",
        numero_ciclo: 1,
        tipo_participacion: "PRINCIPAL",
        estado: "EN_GESTION",
        fecha_inicio: "2026-09-01T10:02:00.000Z",
        fecha_fin: null,
        tipo_cierre: null,
        iniciado_por_id: null,
        iniciado_por_nombres: "Ana Pérez",
        finalizado_por_id: null,
        finalizado_por_nombres: null,
        motivo_cierre: null,
        historial_estados: [],
        participantes: [],
        respuestas: [],
      },
    ];
    const input: LifecycleInput = {
      historial_estados: CLOSED_HISTORIAL,
      areas: [area],
      timeline: [],
      fecha_registro: "2026-09-01T10:00:00.000Z",
      fecha_cierre: null,
      estado: "EN_GESTION",
      now: T("2026-09-10T12:00:00.000Z"),
    };
    const bounds = buildLifecycleBounds(input);
    assert.equal(bounds.hasOpenPeriod, true);
    assert.equal(bounds.dataEnd, bounds.now);
  });

  it("active global state (no open periods) also includes now", () => {
    const input: LifecycleInput = {
      historial_estados: CLOSED_HISTORIAL,
      areas: [emptyArea()],
      timeline: [],
      fecha_registro: "2026-09-01T10:00:00.000Z",
      fecha_cierre: null,
      estado: "EN_GESTION",
      now: T("2026-09-10T12:00:00.000Z"),
    };
    const bounds = buildLifecycleBounds(input);
    assert.equal(bounds.hasOpenPeriod, true);
    assert.equal(bounds.dataEnd, bounds.now);
  });

  it("single event: zero span still gets the floor padding", () => {
    const input: LifecycleInput = {
      historial_estados: [],
      areas: [],
      timeline: [],
      fecha_registro: ISO,
      fecha_cierre: null,
      estado: "ANULADA",
      now: T("2026-09-10T12:00:00.000Z"),
    };
    const bounds = buildLifecycleBounds(input);
    assert.equal(bounds.dataStart, T(ISO));
    assert.equal(bounds.dataEnd, T(ISO));
    assert.ok(bounds.minBound !== null);
    assert.ok(bounds.maxBound !== null);
    assert.equal(bounds.maxBound - bounds.dataEnd, PAD_FLOOR_MS);
  });

  it("same-day trámite keeps the floor padding (hours-long stays visible)", () => {
    const input: LifecycleInput = {
      historial_estados: [],
      areas: [emptyArea()],
      timeline: [],
      fecha_registro: "2026-09-01T10:00:00.000Z",
      fecha_cierre: "2026-09-01T14:30:00.000Z",
      estado: "FINALIZADA",
    };
    const bounds = buildLifecycleBounds(input);
    assert.equal(bounds.hasOpenPeriod, false);
    assert.ok(bounds.dataStart !== null);
    assert.ok(bounds.minBound !== null);
    assert.ok(bounds.maxBound !== null);
    // span is 4h30m; 4% = ~11 min, which is ≥ floor, so padding must be ≥ floor.
    assert.ok(bounds.dataStart - bounds.minBound >= PAD_FLOOR_MS);
  });

  it("empty closed input returns null bounds", () => {
    const input: LifecycleInput = {
      historial_estados: [],
      areas: [],
      timeline: [],
      fecha_registro: null,
      fecha_cierre: null,
      estado: "ANULADA",
    };
    const bounds = buildLifecycleBounds(input);
    assert.deepEqual(
      {
        dataStart: bounds.dataStart,
        dataEnd: bounds.dataEnd,
        minBound: bounds.minBound,
        maxBound: bounds.maxBound,
      },
      {
        dataStart: null,
        dataEnd: null,
        minBound: null,
        maxBound: null,
      },
    );
  });

  it("padding respects the 4% ratio between floor and cap", () => {
    const input: LifecycleInput = {
      historial_estados: [],
      areas: [],
      timeline: [],
      fecha_registro: "2026-01-01T00:00:00.000Z",
      fecha_cierre: "2026-07-01T00:00:00.000Z",
      estado: "FINALIZADA",
    };
    const bounds = buildLifecycleBounds(input);
    assert.ok(bounds.dataStart !== null);
    assert.ok(bounds.dataEnd !== null);
    assert.ok(bounds.minBound !== null);
    const pad = bounds.dataStart - bounds.minBound;
    assert.ok(pad > PAD_FLOOR_MS, "long lifecycle should not be floored");
    assert.ok(
      pad <= 3 * 86_400_000,
      "padding must be capped for long trámites",
    );
  });
});

describe("buildGlobalStateSegments", () => {
  it("closed trámite: contiguous segments ending at dataEnd (F10)", () => {
    const segments = buildGlobalStateSegments(CLOSED_HISTORIAL, {
      dataStart: T("2026-09-01T10:00:00.000Z"),
      dataEnd: T("2026-09-01T10:20:00.000Z"),
      hasOpenPeriod: false,
    });
    assert.equal(segments.length, 3);
    assert.deepEqual(
      segments.map((s) => s.label),
      ["Registrada", "En Gestión", "Finalizada"],
    );
    for (let i = 0; i < segments.length - 1; i += 1) {
      assert.equal(
        segments[i].end,
        segments[i + 1].start,
        "segments must be contiguous",
      );
    }
    assert.equal(
      segments[segments.length - 1].end,
      T("2026-09-01T10:20:00.000Z"),
    );
  });

  it("open trámite: last segment runs to now", () => {
    const segments = buildGlobalStateSegments(
      CLOSED_HISTORIAL,
      {
        dataStart: T("2026-09-01T10:00:00.000Z"),
        dataEnd: T("2026-09-10T12:00:00.000Z"),
        hasOpenPeriod: true,
      },
      T("2026-09-10T12:00:00.000Z"),
    );
    assert.equal(segments.length, 3);
    assert.equal(
      segments[segments.length - 1].end,
      T("2026-09-10T12:00:00.000Z"),
    );
  });

  it("prepends a prologue segment when dataStart predates the first change", () => {
    const historial = CLOSED_HISTORIAL.slice(1);
    const segments = buildGlobalStateSegments(historial, {
      dataStart: T("2026-09-01T10:00:00.000Z"),
      dataEnd: T("2026-09-01T10:20:00.000Z"),
      hasOpenPeriod: false,
    });
    assert.equal(segments[0].id, "segment-initial");
    assert.equal(segments[0].label, "Registrada");
    assert.equal(segments[0].end, T("2026-09-01T10:05:00.000Z"));
  });

  it("returns [] for empty historial", () => {
    const segments = buildGlobalStateSegments([], {
      dataStart: T(ISO),
      dataEnd: T(ISO),
      hasOpenPeriod: false,
    });
    assert.deepEqual(segments, []);
  });

  it("single change: one segment covering the whole range", () => {
    const segments = buildGlobalStateSegments([CLOSED_HISTORIAL[0]], {
      dataStart: T("2026-09-01T10:00:00.000Z"),
      dataEnd: T("2026-09-01T10:20:00.000Z"),
      hasOpenPeriod: false,
    });
    assert.equal(segments.length, 1);
    assert.equal(segments[0].start, T("2026-09-01T10:00:00.000Z"));
    assert.equal(segments[0].end, T("2026-09-01T10:20:00.000Z"));
  });
});

describe("formatDuration", () => {
  it("formats neutral Spanish durations", () => {
    assert.equal(formatDuration(0, 0), "0 min");
    assert.equal(formatDuration(0, 45 * 60_000), "45 min");
    assert.equal(formatDuration(0, 2 * 3_600_000 + 5 * 60_000), "2 h 5 min");
    assert.equal(formatDuration(0, 86_400_000 + 3 * 3_600_000), "1 día 3 h");
    assert.equal(formatDuration(0, 3 * 86_400_000), "3 días");
    assert.equal(
      formatDuration(0, 30 * 86_400_000 + 2 * 86_400_000),
      "1 mes 2 días",
    );
  });

  it("handles open end and negative spans", () => {
    assert.equal(formatDuration(0, null), "En curso");
    assert.equal(formatDuration(100, 0), "0 min");
  });
});

describe("formatTimelineDate", () => {
  const ts = T("2026-09-14T09:05:00.000Z");

  it("defaults to date + time in es-PE", () => {
    const out = formatTimelineDate(ts);
    // es-PE CLDR abbreviates September as "set."; the hour depends on the host TZ.
    assert.match(out, /\d{2} [a-zñ]+\.? 2026/);
    assert.match(out, /,\s*\d{2}:\d{2}/);
  });

  it("day granularity drops the time", () => {
    assert.match(formatTimelineDate(ts, "day"), /\d{2} [a-zñ]+\.? 2026/);
    assert.ok(!formatTimelineDate(ts, "day").includes(":"));
  });

  it("month granularity shows month + year only", () => {
    assert.match(formatTimelineDate(ts, "month"), /^[a-zñ]+\.? 2026$/);
    assert.ok(!formatTimelineDate(ts, "month").includes("09:05"));
  });
});

describe("clampVisibleRange", () => {
  const MIN = T("2026-09-01T00:00:00.000Z");
  const MAX = T("2026-09-10T00:00:00.000Z");

  it("keeps a window that already fits untouched (F07)", () => {
    const start = T("2026-09-02T00:00:00.000Z");
    const end = T("2026-09-05T00:00:00.000Z");
    assert.deepEqual(clampVisibleRange(start, end, MIN, MAX), { start, end });
  });

  it("shifts a window that starts before minBound (left pan is clamped)", () => {
    const span = 2 * DAY_MS;
    const out = clampVisibleRange(
      MIN - 5 * DAY_MS,
      MIN - 5 * DAY_MS + span,
      MIN,
      MAX,
    );
    assert.equal(out.start, MIN);
    assert.equal(out.end, MIN + span);
  });

  it("shifts a window that ends after maxBound (right pan is clamped)", () => {
    const span = 2 * DAY_MS;
    const out = clampVisibleRange(
      MAX + 3 * DAY_MS - span,
      MAX + 3 * DAY_MS,
      MIN,
      MAX,
    );
    assert.equal(out.end, MAX);
    assert.equal(out.start, MAX - span);
  });

  it("preserves the requested duration while clamping", () => {
    const span = 3 * DAY_MS;
    const out = clampVisibleRange(MIN - span, MIN, MIN, MAX);
    assert.equal(out.end - out.start, span);
  });

  it("a window wider than the domain collapses to the full data range", () => {
    const out = clampVisibleRange(
      MIN - 200 * DAY_MS,
      MAX + 200 * DAY_MS,
      MIN,
      MAX,
    );
    assert.deepEqual(out, { start: MIN, end: MAX });
  });

  it("never zooms out into empty years (max zoom-out = full bound)", () => {
    const out = clampVisibleRange(
      MIN - 3650 * DAY_MS,
      MIN - 3650 * DAY_MS + 90 * DAY_MS,
      MIN,
      MAX,
    );
    assert.deepEqual(out, { start: MIN, end: MAX });
  });

  it("degenerate domain returns the domain itself", () => {
    assert.deepEqual(clampVisibleRange(0, 10, 5, 5), { start: 5, end: 5 });
  });
});
