/**
 * TrazabilidadView — top-level traceability view for a Solicitud.
 *
 * Owns the useSolicitudTrazabilidad hook and the SINGLE selection state
 * (audit G, F12/F17; work unit U7): one discriminated `TraceabilitySelection`
 * derived from stable IDs (`global-state`, `area`, `period`,
 * `participant-event`, `response`, `node`). There are no parallel copies:
 *
 * - Card flow (`SolicitudCardFlow`) receives a DERIVED `SolicitudFlowSelection`
 *   (memoized from the single selection — never stale between cycles, F03) and
 *   only highlights the matching branch.
 * - The chronological history (`ChronologicalHistory`) emits global-state
 *   selections on row click.
 * - The single compact inspector (`TraceabilityInspector`, U8) receives the
 *   RESOLVED entities and the full model for disclosure.
 *
 * Composition (top to bottom):
 *   1. TemporalSummary strip (lifecycle: inicio, fin, duración, áreas).
 *   2. SolicitudCardFlow — primary horizontal connected card-map.
 *   3. ChronologicalHistory — collapsed by default, openable via
 *      "Ver historial cronológico".
 *   4. TraceabilityInspector — shown only when a selection is active,
 *      below the flow; not a second rail.
 *
 * No calendar; no React Flow; no duplicate giant panels.
 */
"use client";

import { AlertCircle, FileSearch } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useSolicitudTrazabilidad } from "../../hooks/useTramites";
import type { SolicitudGlobalContext } from "./buildSolicitudFlow";
import { ChronologicalHistory } from "./ChronologicalHistory";
import { SolicitudCardFlow } from "./SolicitudCardFlow";
import { TemporalSummary } from "./TemporalSummary";
import { TraceabilityInspector } from "./TraceabilityInspector";
import {
  resolveSelection,
  type SolicitudFlowSelection,
  type TraceabilitySelection,
  toFlowSelection,
} from "./traceabilitySelection";

// ── Loading skeleton ──────────────────────────────────────────────────────────

function TrazabilidadSkeleton() {
  return (
    <output className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        <div className="h-4 w-32 animate-pulse rounded-md bg-muted" />
        <div className="h-24 animate-pulse rounded-xl border border-border bg-card" />
        <div className="h-24 animate-pulse rounded-xl border border-border bg-card" />
      </div>
    </output>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────

function TrazabilidadError({
  message,
  onRetry,
}: {
  message?: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="h-6 w-6 text-destructive" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-foreground">
          Error al cargar trazabilidad
        </p>
        <p className="text-xs text-muted-foreground">
          {message ?? "No se pudo obtener los datos de trazabilidad."}
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Reintentar
      </Button>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function TrazabilidadEmpty() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <FileSearch
          className="h-6 w-6 text-muted-foreground"
          aria-hidden="true"
        />
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground">
          Sin datos de trazabilidad
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Aún no hay información de trazabilidad para esta solicitud.
        </p>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export interface TrazabilidadViewProps {
  /** The parent Solicitud ID. Fetch is skipped when null. */
  solicitudId: string | null;
  /** Global Solicitud context consumed by the timeline bounds builder (F08). */
  fechaRegistro?: string | null;
  fechaCierre?: string | null;
  estado?: string | null;
  /** Public id (LIMA-2026-0003) for the flow's global start node. */
  idPublico?: string | null;
}

export function TrazabilidadView({
  solicitudId,
  fechaRegistro = null,
  fechaCierre = null,
  estado = null,
  idPublico = null,
}: TrazabilidadViewProps) {
  const { data, isLoading, isError, error, refetch } =
    useSolicitudTrazabilidad(solicitudId);

  // SINGLE selection state — card flow, history and inspector all derive from it.
  const [selection, setSelection] = useState<TraceabilitySelection>(null);
  const focusReturnRef = useRef<HTMLElement | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);

  const globalCtx = useMemo<SolicitudGlobalContext>(
    () => ({
      fecha_registro: fechaRegistro ?? "",
      estado: estado ?? "",
      fecha_cierre: fechaCierre,
      id_publico: idPublico,
    }),
    [fechaRegistro, estado, fechaCierre, idPublico],
  );

  // Derived, never parallel state (F03): switch cycles and the flow
  // always reflects the CURRENT selection, never stale values.
  const flowSelection = useMemo<SolicitudFlowSelection>(
    () => (data ? toFlowSelection(selection, data, globalCtx) : null),
    [selection, data, globalCtx],
  );

  const resolvedSelection = useMemo(
    () => (data ? resolveSelection(selection, data, globalCtx) : null),
    [selection, data, globalCtx],
  );

  function handleSelect(
    next: Exclude<TraceabilitySelection, null>,
    trigger?: HTMLElement,
  ) {
    focusReturnRef.current = trigger ?? null;
    setSelection(next);
  }

  function handleCloseSelection() {
    setSelection(null);
    const trigger = focusReturnRef.current;
    if (trigger && typeof trigger.focus === "function") trigger.focus();
    focusReturnRef.current = null;
  }

  function handleFlowNodeSelect(nodeId: string) {
    setSelection({ type: "node", nodeId });
  }

  // Handle global-state selection from the chronological history.
  function handleHistorySelect(stateId: string) {
    setSelection({ type: "global-state", stateId });
  }

  // Scroll the inspector into view on selection (respect reduced motion).
  useEffect(() => {
    if (!selection) return;
    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    panelRef.current?.scrollIntoView({
      behavior: reduce ? "auto" : "smooth",
      block: "nearest",
    });
  }, [selection]);

  if (isLoading) return <TrazabilidadSkeleton />;

  if (isError) {
    return (
      <TrazabilidadError
        message={error?.message}
        onRetry={() => void refetch()}
      />
    );
  }

  if (!data || (data.areas.length === 0 && data.timeline.length === 0)) {
    return <TrazabilidadEmpty />;
  }

  // Extract selected stateId for the history component's active highlight.
  const selectedStateId =
    selection?.type === "global-state" ? selection.stateId : null;

  return (
    <div className="flex flex-col gap-6">
      {/* 1. TemporalSummary — lifecycle strip */}
      <section aria-label="Resumen temporal">
        <TemporalSummary trazabilidad={data} global={globalCtx} />
      </section>

      {/* 2. SolicitudCardFlow — primary horizontal connected map */}
      <section
        aria-labelledby="flujo-global-heading"
        className="flex flex-col gap-3"
      >
        <h3
          id="flujo-global-heading"
          className="text-sm font-black uppercase tracking-wide text-muted-foreground"
        >
          Flujo de la solicitud
        </h3>
        <SolicitudCardFlow
          trazabilidad={data}
          global={globalCtx}
          selection={flowSelection}
          onNodeSelect={handleFlowNodeSelect}
        />
      </section>

      {/* 3. ChronologicalHistory — collapsed by default */}
      {data.historial_estados.length > 0 && (
        <section aria-label="Historial cronológico">
          <ChronologicalHistory
            historial={data.historial_estados}
            onSelect={handleHistorySelect}
            selectedStateId={selectedStateId}
          />
        </section>
      )}

      {/* 4. Single compact inspector — inside the main column below the flow */}
      {resolvedSelection && (
        <TraceabilityInspector
          selection={resolvedSelection}
          trazabilidad={data}
          onClose={handleCloseSelection}
          containerRef={panelRef}
          onSelectParticipant={handleSelect}
        />
      )}
    </div>
  );
}
