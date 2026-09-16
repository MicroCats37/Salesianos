/**
 * GestionOperativaSolicitud — operational action section for Solicitud detail.
 *
 * Renders below ResumenEjecutivo and before TrazabilidadView.
 * Presentational-only: reuses existing mutations and modal state from the page.
 *
 * Visibility rules (presentation-only, no Guardian/rule changes):
 * - Tomar:       user area matches Solicitud area AND period operable AND user not active participant
 * - Iniciar:     user area matches OR active participant, period PENDIENTE, show inline tile
 * - MarcarErr:   user area matches OR active participant, period EN_GESTION, show inline tile
 * - CambiarPart: user area matches OR active participant, period EN_GESTION, show inline tile
 * - Finalizar:   current rule unchanged — appears in "Cierre de la solicitud" block
 *
 * All period operations (except Tomar) are rendered as inline tiles — NO dropdown.
 * TraceabilityInspector renders informational-only (actions removed from its footer).
 */
"use client";

import {
  AlertTriangle,
  ArrowLeftRight,
  CheckCircle,
  Hand,
  Info,
  PlayCircle,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { PeriodoOperation } from "@/features/asignaciones/components";
import {
  isActiveParticipantInPeriod,
  isUserAssignedToArea,
} from "@/features/tramites/utils/actionVisibility";
import { cn } from "@/lib/utils";
import {
  ESTADO_SOLICITUD,
  TIPO_PARTICIPACION,
  type TipoParticipacion,
} from "@/shared/constants/tramite.tokens";
import type { SolicitudDetail } from "../schemas/tramite.schema";

// ── View model types ───────────────────────────────────────────────────────────

export interface GestionOperativaProps {
  /** Full Solicitud detail (already loaded by parent page). */
  item: SolicitudDetail;
  /** Normalized current user ID (from auth store, already hydrated). */
  currentUserId: string | null;
  /** Normalized area IDs the current user belongs to (from auth store). */
  userAreaIds: Set<string>;
  /** Pre-wired tomar mutation from the page. */
  tomarPeriodo: {
    mutate: (periodoId: string, options?: { onSettled?: () => void }) => void;
    isPending: boolean;
  };
  /** Pre-wired operation handler from the page. */
  onOperationSelect: (periodoId: string, operation: PeriodoOperation) => void;
  /** Whether the current user can finalize the Solicitud (already computed on page). */
  userCanFinalize: boolean;
  /** Handler to open the Finalizar modal. */
  onFinalizar: () => void;
}

// ── Operation tile ─────────────────────────────────────────────────────────────

interface ActionTileProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  onAction: () => void;
  disabled?: boolean;
  isLoading?: boolean;
  variant?: "default" | "destructive";
}

function ActionTile({
  icon: Icon,
  title,
  description,
  onAction,
  disabled,
  isLoading,
  variant = "default",
}: ActionTileProps) {
  return (
    <button
      type="button"
      onClick={onAction}
      disabled={disabled || isLoading}
      className={cn(
        "flex w-full items-start gap-3 rounded-lg border px-3 py-2.5 text-left",
        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        "disabled:pointer-events-none disabled:opacity-50",
        variant === "destructive"
          ? "border-destructive/30 bg-destructive/5 hover:bg-destructive/10"
          : "border-border bg-card hover:bg-muted/40",
      )}
    >
      <div
        className={cn(
          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
          variant === "destructive"
            ? "border-destructive/20 bg-destructive/10"
            : "border-primary/20 bg-primary/10",
        )}
      >
        <Icon
          className={cn(
            "h-4 w-4",
            variant === "destructive" ? "text-destructive" : "text-primary",
          )}
          aria-hidden="true"
        />
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span
          className={cn(
            "text-xs font-semibold",
            variant === "destructive" ? "text-destructive" : "text-foreground",
          )}
        >
          {title}
        </span>
        <span className="text-xs text-muted-foreground">{description}</span>
      </div>
      <Button
        type="button"
        size="sm"
        variant={variant === "destructive" ? "destructive" : "outline"}
        className="h-7 shrink-0 gap-1.5 text-xs"
        disabled={disabled || isLoading}
        onClick={(e) => {
          e.stopPropagation();
          onAction();
        }}
      >
        {isLoading ? (
          <span className="size-3.5 inline-block" aria-hidden="true">
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="size-3.5 rounded-full border border-primary/40 border-t-primary animate-spin" />
            </span>
          </span>
        ) : null}
        Acceder
      </Button>
    </button>
  );
}

// ── Derivation helpers ─────────────────────────────────────────────────────────

const CLOSED_PERIOD_STATES = new Set(["CERRADO", "FINALIZADO", "CANCELADO"]);

interface MatchedPeriod {
  periodoId: string;
  numeroCiclo: number;
  tipoParticipacion: string;
  estado: string;
  estadoLabel: string;
  /** True when period accepts operations (not closed/finalized/cancelled). */
  isOperable: boolean;
  /** True when current user is an active participant in this period. */
  isActiveParticipant: boolean;
  /** True when user belongs to area, not active participant, period operable → show Tomar. */
  showTomar: boolean;
  /** True when user area matches OR active participant, period operable → show operations. */
  showOperations: boolean;
}

interface MatchedArea {
  areaId: string;
  areaNombre: string;
  tipoParticipacion: TipoParticipacion;
  badgeClass: string;
  isMember: boolean;
  /** True when user is active participant in at least one period of this area. */
  hasActiveParticipation: boolean;
  matchedPeriods: MatchedPeriod[];
  /** All periods (matched or not) for informational display. */
  allPeriods: MatchedPeriod[];
}

/**
 * Derive matched areas and periods for the current user from SolicitudDetail.
 * No new fetches — all data comes from `item.asignaciones`.
 */
function deriveViewModel(
  item: SolicitudDetail,
  currentUserId: string | null,
  userAreaIds: Set<string>,
): {
  matchedAreas: MatchedArea[];
  allClosed: boolean;
  hasMatchedAreas: boolean;
  hasActiveParticipation: boolean;
} {
  const matchedAreas: MatchedArea[] = [];

  for (const asignacion of item.asignaciones) {
    const isMember = isUserAssignedToArea(asignacion.area_id, userAreaIds);
    const tipo = (asignacion.periodos?.[0]?.tipo_participacion ??
      "ADJUNTA") as TipoParticipacion;
    const token = TIPO_PARTICIPACION[tipo];

    const allPeriods: MatchedPeriod[] = (asignacion.periodos ?? []).map(
      (periodo) => {
        const isPeriodClosed = CLOSED_PERIOD_STATES.has(periodo.estado);
        const isActiveParticipant = isActiveParticipantInPeriod(
          asignacion.participantes,
          currentUserId,
        );
        const showTomar = isMember && !isActiveParticipant && !isPeriodClosed;
        const showOperations =
          (isMember || isActiveParticipant) && !isPeriodClosed;

        return {
          periodoId: periodo.id,
          numeroCiclo: periodo.numero_ciclo,
          tipoParticipacion: periodo.tipo_participacion,
          estado: periodo.estado,
          estadoLabel:
            ESTADO_SOLICITUD[periodo.estado as keyof typeof ESTADO_SOLICITUD]
              ?.label ?? periodo.estado,
          isOperable: !isPeriodClosed,
          isActiveParticipant,
          showTomar,
          showOperations,
        };
      },
    );

    const matchedPeriods = allPeriods.filter(
      (p) => p.showTomar || p.showOperations,
    );

    const hasActiveParticipation = allPeriods.some(
      (p) => p.isActiveParticipant,
    );

    // Include area if user is a member OR has active participation in any period.
    if (isMember || hasActiveParticipation) {
      matchedAreas.push({
        areaId: asignacion.area_id,
        areaNombre: asignacion.area_nombre,
        tipoParticipacion: tipo,
        badgeClass:
          token?.badgeClass ??
          "bg-muted text-muted-foreground border border-border",
        isMember,
        hasActiveParticipation,
        matchedPeriods,
        allPeriods,
      });
    }
  }

  const allClosed = matchedAreas.every((area) =>
    area.allPeriods.every((p) => !p.isOperable),
  );

  return {
    matchedAreas,
    allClosed,
    hasMatchedAreas: matchedAreas.length > 0,
    hasActiveParticipation: matchedAreas.some((a) => a.hasActiveParticipation),
  };
}

// ── Participation explanations ──────────────────────────────────────────────────

const PARTICIPATION_EXPLANATIONS: Record<string, string> = {
  PRINCIPAL: "El area lidera la atencion de esta solicitud.",
  ADJUNTA:
    "El area participa como soporte porque el asunto tambien le concierne.",
};

function getParticipacionExplicacion(tipo: string): string {
  return (
    PARTICIPATION_EXPLANATIONS[tipo] ?? "Tipo de participacion no especificado."
  );
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

export function GestionOperativaSkeleton() {
  return (
    <div className="app-card p-5 lg:p-6 space-y-4">
      <div className="flex flex-col gap-2">
        <div className="h-4 w-40 rounded bg-muted animate-pulse" />
        <div className="h-3 w-72 rounded bg-muted animate-pulse" />
      </div>
      <div className="flex flex-wrap gap-2">
        <div className="h-8 w-32 rounded bg-muted animate-pulse" />
        <div className="h-8 w-28 rounded bg-muted animate-pulse" />
      </div>
      <div className="h-12 w-full rounded bg-muted animate-pulse" />
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function GestionOperativaSolicitud({
  item,
  currentUserId,
  userAreaIds,
  tomarPeriodo,
  onOperationSelect,
  userCanFinalize,
  onFinalizar,
}: GestionOperativaProps) {
  const [tomandoPeriodoId, setTomandoPeriodoId] = useState<string | null>(null);
  const [loadingOperation, setLoadingOperation] = useState<string | null>(null);

  const { matchedAreas, allClosed, hasMatchedAreas } = deriveViewModel(
    item,
    currentUserId,
    userAreaIds,
  );

  // No auth user yet — show neutral skeleton to avoid flash of "consulta" state.
  if (!currentUserId) {
    return <GestionOperativaSkeleton />;
  }

  const handleTomar = (periodoId: string) => {
    setTomandoPeriodoId(periodoId);
    tomarPeriodo.mutate(periodoId, {
      onSettled: () => setTomandoPeriodoId(null),
    });
  };

  const handleOperation = (
    periodoId: string,
    op: "iniciar-gestion" | "marcar-erronea" | "cambiar-participacion",
  ) => {
    setLoadingOperation(`${periodoId}-${op}`);
    // The page handles the modal opening; we just signal the intent.
    // The modal state is owned by the page, not this component.
    onOperationSelect(periodoId, op);
    setLoadingOperation(null);
  };

  // ── State 1: User has matched areas/participation ───────────────────────────
  if (hasMatchedAreas) {
    const isFinalizable =
      userCanFinalize &&
      item.estado !== "FINALIZADA" &&
      item.estado !== "ANULADA";

    return (
      <section
        aria-labelledby="gestion-operativa-heading"
        className="app-card p-5 lg:p-6 space-y-6"
      >
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1">
            <h2
              id="gestion-operativa-heading"
              className="text-sm font-semibold text-foreground"
            >
              Gestion operativa
            </h2>
            <p className="text-xs text-muted-foreground">
              Tus responsabilidades en esta solicitud
            </p>
          </div>
        </div>

        {/* Tus áreas vinculadas */}
        <div className="flex flex-col gap-3">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Tus areas vinculadas
          </p>
          <div className="flex flex-col gap-2">
            {matchedAreas.map((area) => (
              <div
                key={area.areaId}
                className="flex flex-col gap-1.5 rounded-lg border border-border bg-card px-3 py-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium text-foreground">
                    {area.areaNombre}
                  </span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span
                      className={cn(
                        "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold",
                        area.badgeClass,
                      )}
                    >
                      {TIPO_PARTICIPACION[area.tipoParticipacion]?.label ??
                        area.tipoParticipacion}
                    </span>
                    {area.hasActiveParticipation && (
                      <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                        Participas
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {getParticipacionExplicacion(area.tipoParticipacion)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Acciones disponibles */}
        {matchedAreas.some((a) => a.matchedPeriods.length > 0) ? (
          <div className="flex flex-col gap-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Acciones disponibles
            </p>
            <div className="flex flex-col gap-2">
              {matchedAreas.map((area) =>
                area.matchedPeriods.map((periodo) => (
                  <div
                    key={periodo.periodoId}
                    className="flex flex-col gap-3 rounded-lg border border-border bg-card px-3 py-3"
                  >
                    {/* Context label: area + ciclo + estado */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex min-w-0 flex-col gap-0.5">
                        <span className="truncate text-xs font-medium text-foreground">
                          {area.areaNombre}
                        </span>
                        <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          Ciclo {periodo.numeroCiclo}
                          <span className="text-muted-foreground/50">·</span>
                          <span
                            className={cn(
                              "rounded px-1 py-0.5 text-[10px]",
                              ESTADO_SOLICITUD[
                                periodo.estado as keyof typeof ESTADO_SOLICITUD
                              ]?.badgeClass ??
                                "bg-muted text-muted-foreground border border-border",
                            )}
                          >
                            {periodo.estadoLabel}
                          </span>
                          {periodo.isActiveParticipant && (
                            <span className="text-[10px] font-semibold text-primary">
                              · Tu participacion
                            </span>
                          )}
                        </span>
                      </div>
                      {periodo.showTomar && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 gap-1.5 text-xs shrink-0"
                          aria-label={`Tomar ciclo ${periodo.numeroCiclo} de ${area.areaNombre}`}
                          onClick={() => handleTomar(periodo.periodoId)}
                          disabled={
                            tomandoPeriodoId === periodo.periodoId ||
                            tomarPeriodo.isPending
                          }
                        >
                          {tomandoPeriodoId === periodo.periodoId ? (
                            <span
                              className="size-3.5 inline-block"
                              aria-hidden="true"
                            >
                              <span className="absolute inset-0 flex items-center justify-center">
                                <span className="size-3.5 rounded-full border border-primary/40 border-t-primary animate-spin" />
                              </span>
                            </span>
                          ) : (
                            <Hand className="h-3.5 w-3.5" aria-hidden="true" />
                          )}
                          Tomar
                        </Button>
                      )}
                    </div>

                    {/* Inline action tiles — only when period is EN_GESTION and user is eligible */}
                    {periodo.showOperations &&
                      periodo.estado === "EN_GESTION" && (
                        <div className="flex flex-col gap-2">
                          {/* Marcar como erronea — destructive tile */}
                          <ActionTile
                            icon={AlertTriangle}
                            title="No corresponde a mi area"
                            description="Indica que esta asignacion fue incorrecta. Se registrara el motivo y la asignacion se marca como erronea."
                            onAction={() =>
                              handleOperation(
                                periodo.periodoId,
                                "marcar-erronea",
                              )
                            }
                            isLoading={
                              loadingOperation ===
                              `${periodo.periodoId}-marcar-erronea`
                            }
                            variant="destructive"
                          />
                          {/* Cambiar participacion */}
                          <ActionTile
                            icon={ArrowLeftRight}
                            title="Cambiar participacion"
                            description={`Actualmente: ${TIPO_PARTICIPACION[periodo.tipoParticipacion as TipoParticipacion]?.label ?? periodo.tipoParticipacion}. El ciclo actual se cierra y se abre uno nuevo con el tipo seleccionado.`}
                            onAction={() =>
                              handleOperation(
                                periodo.periodoId,
                                "cambiar-participacion",
                              )
                            }
                            isLoading={
                              loadingOperation ===
                              `${periodo.periodoId}-cambiar-participacion`
                            }
                          />
                        </div>
                      )}

                    {/* Inline action tile — only when period is PENDIENTE and user is eligible */}
                    {periodo.showOperations &&
                      periodo.estado === "PENDIENTE" && (
                        <ActionTile
                          icon={PlayCircle}
                          title="Iniciar gestion"
                          description="Comenzar la atencion de este periodo. El estado cambia a En Gestion."
                          onAction={() =>
                            handleOperation(
                              periodo.periodoId,
                              "iniciar-gestion",
                            )
                          }
                          isLoading={
                            loadingOperation ===
                            `${periodo.periodoId}-iniciar-gestion`
                          }
                        />
                      )}
                  </div>
                )),
              )}
            </div>
          </div>
        ) : allClosed ? (
          <div className="flex items-start gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              No hay acciones pendientes. Los periodos de tus areas vinculadas
              estan cerrados o finalizados.
            </p>
          </div>
        ) : null}

        {/* Cierre de la solicitud */}
        {isFinalizable && (
          <div className="flex flex-col gap-2 rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-3">
            <div className="flex items-start gap-2">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-destructive/20 bg-destructive/10">
                <CheckCircle
                  className="h-4 w-4 text-destructive"
                  aria-hidden="true"
                />
              </div>
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="text-xs font-semibold text-destructive">
                  Cierre de la solicitud
                </span>
                <span className="text-xs text-muted-foreground">
                  Registrar la respuesta formal institucional y cerrar la
                  solicitud. Esta accion no se puede deshacer.
                </span>
              </div>
            </div>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              className="h-8 gap-1.5 text-xs font-semibold self-start"
              onClick={onFinalizar}
            >
              <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
              Finalizar Solicitud
            </Button>
          </div>
        )}
      </section>
    );
  }

  // ── State 2: No matched areas and no active participation — consulta view ───
  return (
    <section
      aria-labelledby="gestion-operativa-heading"
      className="app-card p-5 lg:p-6"
    >
      <div className="flex flex-col gap-1">
        <h2
          id="gestion-operativa-heading"
          className="text-sm font-semibold text-foreground"
        >
          Gestion operativa
        </h2>
        <p className="text-xs text-muted-foreground">
          Tus responsabilidades en esta solicitud
        </p>
      </div>
      <div className="mt-3 flex items-start gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <p className="text-xs text-muted-foreground">
          Vista de consulta. No tienes areas vinculadas ni participacion activa
          en esta solicitud.
        </p>
      </div>
    </section>
  );
}
