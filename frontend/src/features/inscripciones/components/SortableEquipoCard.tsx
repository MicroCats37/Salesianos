"use client";

import { useDroppable } from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  ChevronDown,
  ChevronUp,
  GripVertical,
  MessageSquare,
  Package,
  Pencil,
  Plus,
  Shirt,
  Trash2,
  UserMinus,
  UserPlus,
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

type EquipoItem = InscripcionDetalleOut["equipos"][number];
type ParticipanteItem = EquipoItem["participantes"][number];

interface SortableEquipoCardProps {
  equipo: EquipoItem;
  onAddClick: () => void;
  onYoClick: () => void;
  onEditParticipante: (p: ParticipanteItem) => void;
  onRemoveParticipante: (p: ParticipanteItem) => void;
  expanded: boolean;
  onToggleExpand: () => void;
  activeDragId: string | null;
}

export function SortableEquipoCard({
  equipo,
  onAddClick,
  onYoClick,
  onEditParticipante,
  onRemoveParticipante,
  expanded,
  onToggleExpand,
  activeDragId,
}: SortableEquipoCardProps) {
  // Drop zone so other teams' participants can be dropped here.
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `equipo-drop-${equipo.id}`,
    data: { type: "equipo", equipoId: equipo.id },
  });

  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <div
        ref={setDropRef}
        data-equipo-id={equipo.id}
        className={cn(
          "rounded-xl border bg-white shadow-sm transition-all duration-200",
          isOver
            ? "border-primary ring-4 ring-primary/30 bg-primary/5 scale-[1.005]"
            : "border-gray-200 hover:border-gray-300",
        )}
      >
        {/* Header */}
        <div className="flex items-start gap-3 p-5 pb-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
            <Package className="size-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-gray-900 truncate">
              {equipo.nombre}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                {equipo.disciplina.sigla}
              </span>
              <span className="text-sm text-gray-500">
                {equipo.disciplina.nombre}
              </span>
            </div>
            {equipo.categoria && (
              <p className="text-xs text-gray-400 mt-0.5">
                Categoría: {equipo.categoria.nombre}
              </p>
            )}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="flex items-center gap-1.5 rounded-full bg-sky-50 px-2.5 py-1.5 cursor-default"
                  title={`${equipo.participantes.length} jugadores en este equipo`}
                >
                  <Users className="size-3.5 text-sky-600" />
                  <span className="text-xs font-semibold text-sky-700 tabular-nums">
                    {equipo.participantes.length}
                  </span>
                </div>
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
                  variant="outline"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddClick();
                  }}
                  className="h-9 w-9 rounded-lg border-primary/30 text-primary hover:bg-primary/10"
                  aria-label={`Agregar jugador al equipo ${equipo.nombre}`}
                >
                  <Plus className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold">Agregar jugador</p>
                <p className="text-[11px] opacity-80">
                  Abre el formulario completo (identidad, contacto, notas).
                </p>
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
                    onYoClick();
                  }}
                  className="h-9 w-9 rounded-lg border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                  aria-label={`Agregarme al equipo ${equipo.nombre}`}
                >
                  <UserPlus className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold">Agregarme a este equipo</p>
                <p className="text-[11px] opacity-80">
                  Te inscribes como jugador (puedes elegir rol y dejar una
                  nota).
                </p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand();
                  }}
                  className="h-9 w-9 rounded-lg"
                  aria-label={expanded ? "Contraer lista" : "Expandir lista"}
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

        {/* Body — collapsible participant list */}
        {expanded && (
          <div className="px-5 pb-5">
            {equipo.participantes.length > 0 ? (
              <SortableContext
                items={equipo.participantes.map((p) => p.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="divide-y divide-gray-100 border-t border-gray-100">
                  {equipo.participantes.map((p) => (
                    <SortableParticipanteRow
                      key={p.id}
                      participante={p}
                      equipoId={equipo.id}
                      onEdit={() => onEditParticipante(p)}
                      onRemove={() => onRemoveParticipante(p)}
                      activeDragId={activeDragId}
                    />
                  ))}
                </div>
              </SortableContext>
            ) : (
              <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50/50 py-6 text-center">
                <p className="text-xs text-gray-500 italic">
                  Sin participantes registrados. Toca el{" "}
                  <Plus className="inline size-3 align-middle" /> para agregar o
                  el{" "}
                  <UserPlus className="inline size-3 align-middle text-emerald-600" />{" "}
                  para sumarte.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Drop hint when over with active drag from another team */}
        {isOver && activeDragId && (
          <div className="mx-5 mb-5 rounded-lg border-2 border-dashed border-primary bg-primary/10 px-3 py-3 text-sm text-primary font-bold flex items-center gap-2 animate-pulse">
            <UserMinus className="size-4" />
            Suelta aquí para mover a este equipo
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}

interface SortableParticipanteRowProps {
  participante: ParticipanteItem;
  equipoId: string;
  onEdit: () => void;
  onRemove: () => void;
  activeDragId: string | null;
}

function SortableParticipanteRow({
  participante,
  equipoId,
  onEdit,
  onRemove,
  activeDragId,
}: SortableParticipanteRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: participante.id,
    data: { type: "participante", equipoId },
  });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 20 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "group flex items-center gap-2 py-2 transition-colors hover:bg-muted/30 rounded-md",
        activeDragId === participante.id && "ring-2 ring-primary/40 rounded",
      )}
    >
      {/* Drag handle */}
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            aria-label={`Mover o reordenar a ${participante.persona.nombres}`}
            {...attributes}
            {...listeners}
            className="flex h-8 w-6 cursor-grab items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary active:cursor-grabbing shrink-0"
          >
            <GripVertical className="size-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent side="left">
          <p className="font-semibold">Arrastra para mover</p>
          <p className="text-[11px] opacity-80">
            Suelta sobre otro equipo para reasignarlo
          </p>
        </TooltipContent>
      </Tooltip>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <p className="font-medium text-gray-900 truncate">
            {participante.persona.nombres} {participante.persona.apellidos}
          </p>
          {participante.notas?.trim() && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span
                  className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-1.5 py-0.5 text-[10px] font-semibold text-violet-700 shrink-0 cursor-help"
                  title="Tiene notas internas"
                >
                  <MessageSquare className="size-2.5" />
                  Nota
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="font-semibold mb-1">Notas internas</p>
                <p className="text-xs leading-snug whitespace-pre-wrap">
                  {participante.notas}
                </p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <p className="text-xs text-gray-500">
          {participante.persona.numero_documento}
        </p>
      </div>

      <div className="text-right flex flex-col items-end gap-0.5 shrink-0">
        <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
          {participante.rol}
        </span>
        {participante.talle_camiseta && (
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <Shirt className="size-3" />
            {participante.talle_camiseta}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1 shrink-0">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={onEdit}
              className="h-8 w-8 text-muted-foreground hover:text-primary"
              aria-label={`Editar a ${participante.persona.nombres}`}
            >
              <Pencil className="size-3.5" />
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
              className="h-8 w-8 text-muted-foreground hover:text-destructive"
              aria-label={`Eliminar a ${participante.persona.nombres}`}
            >
              <Trash2 className="size-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p className="font-semibold">Eliminar del equipo</p>
            <p className="text-[11px] opacity-80">
              Te pedirá confirmar antes de borrar
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}
