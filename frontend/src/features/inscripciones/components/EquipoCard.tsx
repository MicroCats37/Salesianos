"use client";

import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Package,
  Pencil,
  Plus,
  Shirt,
  Trash2,
  UserRound,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";
import { poolGuiaEquipoVacio } from "../utils/pool.primero";

type EquipoItem = InscripcionDetalleOut["equipos"][number];
type ParticipanteItem = EquipoItem["participantes"][number];

interface EquipoCardProps {
  equipo: EquipoItem;
  /** Opens the participant selector for this team. */
  onAsignarClick: () => void;
  onEditParticipante: (p: ParticipanteItem) => void;
  onRemoveParticipante: (p: ParticipanteItem) => void;
  expanded: boolean;
  onToggleExpand: () => void;
  /**
   * How many people the BACKEND reports as assignable to THIS team.
   *
   * `undefined` means "not known yet" (the list is loading): the action stays
   * enabled so the responsable is never blocked by a pending request. `0`
   * means there is nobody to add — the action is disabled and the tooltip
   * explains WHY instead of opening an empty selector.
   */
  asignables?: number;
  /** Reason shown when there is nobody to add (backend wording). */
  motivoSinAsignables?: string | null;
}

/**
 * Card of one team with its roster.
 *
 * The assignment gesture is the participant selector modal (see
 * `SelectorParticipanteModal`), NOT a drag-and-drop: drag implied "move",
 * and moving a player out of a discipline is not what the responsable means
 * when the same person may legitimately play in several disciplines.
 *
 * The card has NO creation action: a participant is registered in the pool
 * and then ASSIGNED here. The only team-level action is the selector.
 */
export function EquipoCard({
  equipo,
  onAsignarClick,
  onEditParticipante,
  onRemoveParticipante,
  expanded,
  onToggleExpand,
  asignables,
  motivoSinAsignables,
}: EquipoCardProps) {
  const completo = equipo.estado_roster === "COMPLETO";
  const registrados = equipo.jugadores_registrados;
  const minimo = equipo.minimo_deportivo;
  const progreso =
    minimo > 0 ? Math.min(100, Math.round((registrados / minimo) * 100)) : 100;

  /** Nobody can be added: the action is disabled with the real reason. */
  const sinAsignables = asignables === 0;
  const motivoSinGente =
    motivoSinAsignables ??
    "No hay participantes con cupo pagado que puedan entrar a este equipo.";

  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <article
        data-equipo-id={equipo.id}
        className="overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-sm transition-all duration-300 hover:border-[#312e8e]/25 hover:shadow-lg"
      >
        {/* ── Header ── */}
        <header className="flex flex-col gap-4 p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3 sm:gap-4">
              <span className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
                <Package className="size-5" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-[#312e8e]/10 px-2.5 py-0.5 text-[11px] font-black uppercase tracking-wider text-[#312e8e]">
                    {equipo.disciplina.sigla}
                  </span>
                  {equipo.categoria && (
                    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
                      {equipo.categoria.nombre}
                    </span>
                  )}
                </div>
                <h3 className="mt-1.5 text-lg font-black tracking-tight text-slate-900 sm:text-xl">
                  {equipo.nombre}
                </h3>
                <p className="text-xs text-slate-500">
                  {equipo.disciplina.nombre}
                </p>
              </div>
            </div>

            {/* ── Actions ── grouped right on desktop, stacked on mobile ── */}
            <div className="flex shrink-0 items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    className="inline-flex h-11 items-center gap-1.5 rounded-full bg-sky-50 px-3 text-xs font-semibold text-sky-700"
                    title={`${equipo.participantes.length} jugadores en este equipo`}
                  >
                    <Users className="size-3.5" />
                    <span className="tabular-nums">
                      {equipo.participantes.length}
                    </span>
                    <span className="sr-only">jugadores en este equipo</span>
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>
                    {equipo.participantes.length}{" "}
                    {equipo.participantes.length === 1
                      ? "jugador registrado"
                      : "jugadores registrados"}{" "}
                    en este equipo
                  </p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAsignarClick();
                    }}
                    disabled={sinAsignables}
                    className={cn(
                      "btn-brand-gradient btn-shine h-11 flex-1 rounded-full px-4 text-xs font-black uppercase tracking-wider sm:flex-none",
                      sinAsignables &&
                        "bg-slate-100 text-slate-400 shadow-none ring-1 ring-slate-200",
                    )}
                    aria-label={`Agregar jugador al equipo ${equipo.nombre}`}
                  >
                    <Plus className="size-4" />
                    Agregar
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  {sinAsignables ? (
                    <>
                      <p className="font-semibold">No hay nadie para agregar</p>
                      <p className="text-[11px] opacity-80">{motivoSinGente}</p>
                    </>
                  ) : (
                    <>
                      <p className="font-semibold">Agregar jugador</p>
                      <p className="text-[11px] opacity-80">
                        Abre el selector de participantes del equipo.
                      </p>
                    </>
                  )}
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleExpand();
                    }}
                    className="size-11 shrink-0 rounded-full border-slate-200 text-slate-600 hover:bg-slate-50"
                    aria-label={
                      expanded
                        ? `Contraer la lista de ${equipo.nombre}`
                        : `Expandir la lista de ${equipo.nombre}`
                    }
                  >
                    {expanded ? (
                      <ChevronUp className="size-4" />
                    ) : (
                      <ChevronDown className="size-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>{expanded ? "Contraer lista" : "Expandir lista"}</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* ── Roster progress ── presenter-derived, no business logic here ── */}
          <div className="rounded-2xl bg-slate-50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                  Jugadores
                </span>
                <span className="text-base font-black tabular-nums text-slate-900">
                  {registrados}
                  <span className="text-slate-500">/{minimo}</span>
                </span>
              </div>
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-bold",
                  completo
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-amber-200 bg-amber-50 text-amber-700",
                )}
                title={`Roster: ${equipo.estado_roster}`}
              >
                {completo ? (
                  <CheckCircle2 className="size-3.5" />
                ) : (
                  <Users className="size-3.5" />
                )}
                {completo
                  ? "Roster completo"
                  : `${equipo.faltantes} faltante${equipo.faltantes !== 1 ? "s" : ""}`}
              </span>
            </div>
            <div
              className="mt-2.5 h-2 w-full overflow-hidden rounded-full bg-slate-200/80"
              role="progressbar"
              aria-valuenow={registrados}
              aria-valuemin={0}
              aria-valuemax={minimo}
              aria-label={`Jugadores registrados de ${equipo.nombre}`}
            >
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  completo
                    ? "bg-gradient-to-r from-emerald-400 to-emerald-600"
                    : "bg-gradient-to-r from-[#312e8e] to-[#6976ff]",
                )}
                style={{ width: `${progreso}%` }}
              />
            </div>
          </div>
        </header>

        {/* ── Body — collapsible participant list ── */}
        {expanded && (
          <div className="border-t border-slate-100 px-5 py-4 sm:px-6">
            {equipo.participantes.length > 0 ? (
              <ul className="divide-y divide-slate-100">
                {equipo.participantes.map((p) => (
                  <ParticipanteRow
                    key={p.id}
                    participante={p}
                    onEdit={() => onEditParticipante(p)}
                    onRemove={() => onRemoveParticipante(p)}
                  />
                ))}
              </ul>
            ) : (
              <div className="rounded-2xl border border-dashed border-amber-300 bg-amber-50/50 px-4 py-7 text-center">
                <span className="mx-auto flex size-11 items-center justify-center rounded-2xl bg-white text-amber-600 shadow-sm">
                  <UserRound className="size-5" />
                </span>
                <p className="mt-3 text-sm font-bold text-amber-900">
                  {poolGuiaEquipoVacio().titulo}
                </p>
                <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-amber-900/80">
                  {poolGuiaEquipoVacio().descripcion}
                </p>
                <p className="mt-2 text-xs text-amber-700/80">
                  Toca el boton <Plus className="inline size-3 align-middle" />{" "}
                  para abrir el selector de participantes.
                </p>
              </div>
            )}
          </div>
        )}
      </article>
    </TooltipProvider>
  );
}

interface ParticipanteRowProps {
  participante: ParticipanteItem;
  onEdit: () => void;
  onRemove: () => void;
}

function ParticipanteRow({
  participante,
  onEdit,
  onRemove,
}: ParticipanteRowProps) {
  const nombre = `${participante.persona?.nombres ?? ""} ${
    participante.persona?.apellidos ?? ""
  }`.trim();
  const iniciales = inicialesDe(nombre);
  const conNotas = Boolean(participante.notas?.trim());

  return (
    <li className="flex items-center gap-3 py-3">
      <span
        aria-hidden="true"
        className="flex size-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#312e8e] to-[#25236f] text-xs font-black uppercase text-white"
      >
        {iniciales || "?"}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <p className="truncate text-sm font-bold text-slate-900">
            {nombre || "—"}
          </p>
          {conNotas && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-violet-100 px-1.5 py-0.5 text-[10px] font-semibold text-violet-700">
                  <MessageSquare className="size-2.5" />
                  Nota
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="mb-1 font-semibold">Notas internas</p>
                <p className="whitespace-pre-wrap text-xs leading-snug">
                  {participante.notas}
                </p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <p className="flex items-center gap-2 text-xs text-slate-500">
          <span>{participante.persona?.numero_documento ?? "—"}</span>
          {participante.talla_camiseta && (
            <span className="inline-flex items-center gap-1">
              <Shirt className="size-3" />
              {participante.talla_camiseta}
            </span>
          )}
        </p>
      </div>

      <span className="inline-flex shrink-0 items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
        {participante.rol}
      </span>

      <div className="flex shrink-0 items-center gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onEdit}
              className="size-11 rounded-full text-muted-foreground hover:text-primary"
              aria-label={`Editar a ${participante.persona?.nombres ?? "este jugador"}`}
            >
              <Pencil className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p>Editar jugador (rol, talle, notas)</p>
          </TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onRemove}
              className="size-11 rounded-full text-muted-foreground hover:text-destructive"
              aria-label={`Eliminar a ${participante.persona?.nombres ?? "este jugador"}`}
            >
              <Trash2 className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p className="font-semibold">Eliminar del equipo</p>
            <p className="text-[11px] opacity-80">
              Te pedira confirmar antes de borrar
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
    </li>
  );
}

/** Two-letter monogram of a full name. */
function inicialesDe(nombre: string): string {
  const partes = nombre.split(" ").filter(Boolean);
  if (partes.length === 0) return "";
  const primera = partes[0].charAt(0);
  const segunda = partes.length > 1 ? partes[partes.length - 1].charAt(0) : "";
  return `${primera}${segunda}`.toUpperCase();
}
