/**
 * SolicitudCardFlow — CSS-only horizontal card-based flow (mind-map style).
 *
 * Design decisions:
 * - Horizontal left-to-right flow with global rail at top and area branches below.
 * - No graph library; connectors are pure CSS using `::before`/`::after` pseudo-elements
 *   with borders (border-right + border-top for arrows).
 * - Visual grouping by area via subtle background bands.
 * - Selection: single click highlights the card with `data-selected` and emits the node id
 *   via `onNodeSelect` — same contract as the replaced React Flow.
 * - Dimming: cards not in the selected branch get `data-dimmed="true"` via CSS attribute
 *   selectors; this is computed once per render and applied via inline styles.
 * - Responsive: horizontal scroll inside the container; no page-level overflow.
 */

"use client";

import {
  ArrowRight,
  CheckCircle2,
  Circle,
  GitBranch,
  LogIn,
  LogOut,
  Play,
  UserPlus,
  UsersRound,
} from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { useCallback, useMemo } from "react";

import { cn } from "@/lib/utils";
import type { SolicitudTrazabilidad } from "../../schemas/trazabilidad.schema";
import {
  buildSolicitudFlow,
  type FlowNode,
  type FlowNodeKind,
  type SolicitudFlow,
  type SolicitudGlobalContext,
} from "./buildSolicitudFlow";
import type { SolicitudFlowSelection } from "./traceabilitySelection";
import { formatTimelineDate } from "./traceabilityTimeline";

// ── Props ────────────────────────────────────────────────────────────────────────

export interface SolicitudCardFlowProps {
  /** Full traceability payload — used to build the flow graph. */
  trazabilidad: SolicitudTrazabilidad;
  /** Global Solicitud context (fecha_registro, estado, fecha_cierre, id_publico). */
  global: SolicitudGlobalContext;
  /** Current highlight/center selection from the unified selection model. */
  selection: SolicitudFlowSelection;
  /** Called when a card is clicked; drives the single-selection state. */
  onNodeSelect: (nodeId: string) => void;
}

// ── Data building ────────────────────────────────────────────────────────────────

function safeMs(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

// ── Dimming logic ────────────────────────────────────────────────────────────────

/** Determine if a node is outside the selected branch (dimmed). */
function isDimmed(node: FlowNode, selection: SolicitudFlowSelection): boolean {
  if (!selection) return false;
  switch (selection.type) {
    case "area":
      // Dim everything except the selected area's branch
      return node.areaId !== selection.areaId;
    case "period":
      return (
        node.areaId !== selection.areaId || node.periodId !== selection.periodId
      );
    case "node":
      // Dim everything except the selected node itself
      return node.id !== selection.nodeId;
    default:
      return false;
  }
}

// ── Icon mapping ─────────────────────────────────────────────────────────────────

const KIND_ICONS: Record<
  FlowNodeKind,
  ComponentType<{ className?: string }>
> = {
  "global-start": Play,
  "global-state": Circle,
  "global-merge": GitBranch,
  "global-terminal": CheckCircle2,
  "area-start": LogIn,
  "area-terminal": LogOut,
  "period-start": Circle,
  "period-terminal": Circle,
  "participant-added": UserPlus,
  "participant-removed": UsersRound,
  response: CheckCircle2,
  "period-state-change": ArrowRight,
};

const KIND_COLORS: Record<FlowNodeKind, string> = {
  "global-start": "text-primary",
  "global-state": "text-primary",
  "global-merge": "text-muted-foreground",
  "global-terminal": "text-primary",
  "area-start": "text-blue-600",
  "area-terminal": "text-muted-foreground",
  "period-start": "text-amber-600",
  "period-terminal": "text-muted-foreground",
  "participant-added": "text-green-600",
  "participant-removed": "text-orange-500",
  response: "text-violet-600",
  "period-state-change": "text-cyan-600",
};

// ── Timestamp formatter ─────────────────────────────────────────────────────────────

function formatCardTimestamp(ts: string): string {
  const ms = safeMs(ts);
  if (ms === null) return "";
  return formatTimelineDate(ms, "minutes");
}

// ── Card component ───────────────────────────────────────────────────────────────

interface FlowCardProps {
  node: FlowNode;
  selected: boolean;
  dimmed: boolean;
  onSelect: (nodeId: string) => void;
  /** "global" | "area" | "period" | "event" */
  cardType: "global" | "area" | "period" | "event";
  isLast?: boolean;
}

function FlowCard({
  node,
  selected,
  dimmed,
  onSelect,
  cardType,
  isLast = false,
}: FlowCardProps) {
  const Icon = KIND_ICONS[node.kind] ?? Circle;
  const iconColor = KIND_COLORS[node.kind] ?? "text-muted-foreground";

  const handleClick = useCallback(() => {
    onSelect(node.id);
  }, [node.id, onSelect]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect(node.id);
      }
    },
    [node.id, onSelect],
  );

  const isOpen = node.open === true;
  const ts = formatCardTimestamp(node.timestamp);

  return (
    <button
      type="button"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${node.label}${node.sublabel ? `, ${node.sublabel}` : ""}${ts ? `, ${ts}` : ""}`}
      aria-pressed={selected}
      data-kind={node.kind}
      data-selected={selected ? "true" : undefined}
      data-dimmed={dimmed ? "true" : undefined}
      data-card-type={cardType}
      className={cn(
        // Base card styles
        "relative flex min-w-[140px] max-w-[200px] flex-col gap-1 rounded-lg border px-3 py-2.5 text-left",
        "transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        // Selected state
        selected
          ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/30"
          : "border-border bg-card",
        // Dimmed state
        dimmed && "opacity-40",
        // Open period indicator
        isOpen && "border-primary/40 border-l-2 border-l-primary",
        // Global cards
        cardType === "global" && "min-w-[160px]",
        // Area cards
        cardType === "area" && "min-w-[150px]",
        // Period cards
        cardType === "period" && "min-w-[140px]",
        // Event cards
        cardType === "event" && "min-w-[130px]",
      )}
    >
      {/* Right connector arrow — hidden on last card of each group */}
      {!isLast && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute -right-3 top-1/2 z-10 flex size-3 items-center justify-center"
          style={{ transform: "translateX(50%)" }}
        >
          <ArrowRight className="size-3 text-muted-foreground/60" />
        </span>
      )}

      {/* Header row: icon + kind badge */}
      <div className="flex items-center justify-between gap-1.5">
        <Icon className={cn("size-4 shrink-0", iconColor)} />
        {isOpen && (
          <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold text-primary">
            En curso
          </span>
        )}
      </div>

      {/* Main label */}
      <span className="text-[11px] font-semibold leading-tight text-foreground">
        {node.label}
      </span>

      {/* Sublabel */}
      {node.sublabel && (
        <span className="text-[10px] leading-tight text-muted-foreground">
          {node.sublabel}
        </span>
      )}

      {/* Timestamp */}
      {ts && <span className="text-[10px] text-muted-foreground/80">{ts}</span>}
    </button>
  );
}

// ── Area band component ──────────────────────────────────────────────────────────

interface AreaBandProps {
  areaId: string;
  areaNombre: string;
  tipoActual: string | null;
  cards: ReactNode;
  selected: boolean;
  dimmed: boolean;
}

function AreaBand({
  areaNombre,
  tipoActual,
  cards,
  selected,
  dimmed,
}: AreaBandProps) {
  const tipoBadge =
    tipoActual === "PRINCIPAL"
      ? "Principal"
      : tipoActual === "ADJUNTA"
        ? "Adjunta"
        : null;

  return (
    <div
      className={cn(
        "relative flex flex-col gap-2 rounded-xl border p-3",
        selected
          ? "border-primary/40 bg-primary/5"
          : "border-border/60 bg-muted/20",
        dimmed && "opacity-40",
      )}
      data-area-band="true"
    >
      {/* Area header */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-foreground truncate">
          {areaNombre}
        </span>
        {tipoBadge && (
          <span
            className={cn(
              "shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-semibold",
              tipoActual === "PRINCIPAL"
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground",
            )}
          >
            {tipoBadge}
          </span>
        )}
      </div>

      {/* Cards row */}
      <div className="flex flex-wrap gap-2">{cards}</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────────

export function SolicitudCardFlow({
  trazabilidad,
  global,
  selection,
  onNodeSelect,
}: SolicitudCardFlowProps) {
  // Build the flow graph from the pure builder
  const flow = useMemo<SolicitudFlow>(
    () => buildSolicitudFlow(trazabilidad, global),
    [trazabilidad, global],
  );

  // ── Partition nodes ──────────────────────────────────────────────────────────
  const globalNodes = useMemo<FlowNode[]>(
    () =>
      flow.nodes.filter(
        (n) =>
          n.kind === "global-start" ||
          n.kind === "global-state" ||
          n.kind === "global-merge" ||
          n.kind === "global-terminal",
      ),
    [flow.nodes],
  );

  const areaBranches = useMemo(
    () =>
      flow.areaGroups.map((group) => {
        const areaNodes = flow.nodes.filter((n) => n.areaId === group.areaId);
        // Split area nodes into: area-start, periods+events, area-terminal
        const areaStart = areaNodes.find((n) => n.kind === "area-start");
        const areaTerminal = areaNodes.find((n) => n.kind === "area-terminal");
        const periodAndEvents = areaNodes.filter(
          (n) => n.kind !== "area-start" && n.kind !== "area-terminal",
        );
        return { group, areaStart, areaTerminal, periodAndEvents };
      }),
    [flow.areaGroups, flow.nodes],
  );

  // ── Render helper ────────────────────────────────────────────────────────────
  const renderCard = useCallback(
    (
      node: FlowNode,
      cardType: "global" | "area" | "period" | "event",
      isLast = false,
    ) => {
      const selected =
        selection?.type === "node" && selection.nodeId === node.id;
      const dimmed = isDimmed(node, selection);
      return (
        <FlowCard
          key={node.id}
          node={node}
          selected={selected}
          dimmed={dimmed}
          onSelect={onNodeSelect}
          cardType={cardType}
          isLast={isLast}
        />
      );
    },
    [selection, onNodeSelect],
  );

  // ── Global rail ────────────────────────────────────────────────────────────
  const globalRail = (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      {globalNodes.map((node, idx) =>
        renderCard(node, "global", idx === globalNodes.length - 1),
      )}
    </div>
  );

  // ── Area branches ────────────────────────────────────────────────────────────
  const areaBands = areaBranches.map(
    ({ group, areaStart, areaTerminal, periodAndEvents }) => {
      const selected =
        selection?.type === "area" && selection.areaId === group.areaId;
      const dimmed = isDimmed(
        {
          id: group.areaId,
          kind: "area-start",
          label: "",
          timestamp: "",
          handles: { input: false, output: false },
        },
        selection,
      );

      // Build the card sequence for this area
      const cards: ReactNode[] = [];

      if (areaStart) {
        cards.push(renderCard(areaStart, "area"));
      }

      // Group periodAndEvents by periodId
      const periodGroups = new Map<string, FlowNode[]>();
      for (const node of periodAndEvents) {
        const key = node.periodId ?? "__orphan__";
        const existing = periodGroups.get(key) ?? [];
        existing.push(node);
        periodGroups.set(key, existing);
      }

      for (const [, groupNodes] of periodGroups) {
        // Sort by KIND_RANK (period-start first, then inner events, then period-terminal)
        const KIND_RANK: Record<FlowNodeKind, number> = {
          "global-start": 0,
          "global-state": 1,
          "area-start": 2,
          "period-start": 10,
          "participant-added": 20,
          "period-state-change": 21,
          response: 22,
          "participant-removed": 23,
          "period-terminal": 30,
          "area-terminal": 40,
          "global-merge": 50,
          "global-terminal": 60,
        };
        const sorted = [...groupNodes].sort((a, b) => {
          const ra = KIND_RANK[a.kind] ?? 99;
          const rb = KIND_RANK[b.kind] ?? 99;
          if (ra !== rb) return ra - rb;
          return a.id < b.id ? -1 : 1;
        });

        for (let i = 0; i < sorted.length; i++) {
          const node = sorted[i];
          const isLastInGroup = i === sorted.length - 1;
          const cardType: "period" | "event" =
            node.kind === "period-start" || node.kind === "period-terminal"
              ? "period"
              : "event";
          cards.push(renderCard(node, cardType, isLastInGroup));
        }
      }

      if (areaTerminal) {
        cards.push(renderCard(areaTerminal, "area", true));
      }

      return (
        <AreaBand
          key={group.areaId}
          areaId={group.areaId}
          areaNombre={group.areaNombre}
          tipoActual={group.tipoActual}
          cards={cards}
          selected={!!selected}
          dimmed={dimmed}
        />
      );
    },
  );

  // ── Legend ───────────────────────────────────────────────────────────────────
  const Legend = (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg border border-border/40 bg-muted/20 px-3 py-2 text-[10px] text-muted-foreground">
      <span className="font-semibold">Flujo operativo:</span>
      <span>Las conexiones muestran precedencia cronologica registrada</span>
      <span className="text-muted-foreground/60">|</span>
      <span className="flex items-center gap-1">
        <span className="size-2 rounded-full bg-primary" /> Inicio / Estado
      </span>
      <span className="flex items-center gap-1">
        <span className="size-2 rounded-full bg-blue-600" /> Area
      </span>
      <span className="flex items-center gap-1">
        <span className="size-2 rounded-full bg-amber-600" /> Ciclo
      </span>
      <span className="flex items-center gap-1">
        <span className="size-2 rounded-full bg-green-600" /> Participante
      </span>
      <span className="flex items-center gap-1">
        <span className="size-2 rounded-full bg-violet-600" /> Respuesta
      </span>
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      {Legend}
      {/* Global rail */}
      <div className="flex flex-col gap-1">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
          Estado de la solicitud
        </span>
        {globalRail}
      </div>

      {/* Connector from global to areas */}
      {areaBands.length > 0 && (
        <div className="relative flex flex-col gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Areas y ciclos
          </span>
          {/* Vertical connector line from global rail to area bands */}
          <div className="flex flex-col gap-2">{areaBands}</div>
        </div>
      )}
    </div>
  );
}
