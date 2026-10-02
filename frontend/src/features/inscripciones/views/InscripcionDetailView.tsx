"use client";

import {
  closestCorners,
  DndContext,
  type DragEndEvent,
  DragOverlay,
  type DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import {
  AlertCircle,
  ArrowLeft,
  CreditCard,
  GraduationCap,
  GripVertical,
  Info,
  MessageSquare,
  MousePointerClick,
  Package,
  Save,
  Users,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { IzipayModal } from "@/features/pagos";
import { cn } from "@/lib/utils";
import { AddParticipanteModal } from "../components/AddParticipanteModal";
import { AgregarmeModal } from "../components/AgregarmeModal";
import { EditParticipanteModal } from "../components/EditParticipanteModal";
import { RegistrationStepsCard } from "../components/RegistrationStepsCard";
import { SortableEquipoCard } from "../components/SortableEquipoCard";
import { useInscripcionCacheSync } from "../hooks/useInscripcionCacheSync";
import { useInscripcionDetalle } from "../hooks/useInscripcionDetalle";
import type { ParticipanteFormData } from "../schemas/participante.schema";
import {
  agregarParticipantesAEquipo,
  eliminarParticipante,
  type InscripcionDetalleOut,
  moverParticipante,
} from "../services/inscripcion.service";

type EquipoItem = InscripcionDetalleOut["equipos"][number];
type ParticipanteItem = EquipoItem["participantes"][number];

type DraftItem = ParticipanteFormData & { _key: string };

function HeroField({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value?: string | null;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400/20 text-amber-300">
        <Icon className="size-5" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/60">
          {label}
        </p>
        <p className="truncate text-sm font-bold text-white">{value ?? "-"}</p>
      </div>
    </div>
  );
}

function SummaryItem({
  label,
  value,
  secondary,
}: {
  label: string;
  value: string;
  secondary?: string | null;
}) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
        {label}
      </p>
      <p className="text-sm font-bold text-slate-900">{value}</p>
      {secondary && <p className="text-xs text-slate-500">{secondary}</p>}
    </div>
  );
}

function estadoBadgeLight(estado: string) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-black uppercase tracking-wider text-white">
      {estado.replace(/_/g, " ")}
    </span>
  );
}

function estadoBadge(estado: string) {
  const map: Record<string, { label: string; className: string }> = {
    RECIBIDA: {
      label: "Recibida",
      className: "bg-blue-100 text-blue-800 border-blue-200",
    },
    CONFIRMADA: {
      label: "Confirmada",
      className: "bg-green-100 text-green-800 border-green-200",
    },
    PENDIENTE: {
      label: "Pendiente",
      className: "bg-yellow-100 text-yellow-800 border-yellow-200",
    },
    PAGO_PENDIENTE: {
      label: "Pago Pendiente",
      className: "bg-orange-100 text-orange-800 border-orange-200",
    },
    PAGADA: {
      label: "Pagada",
      className: "bg-green-100 text-green-800 border-green-200",
    },
    CANCELADA: {
      label: "Cancelada",
      className: "bg-red-100 text-red-800 border-red-200",
    },
  };
  const style = map[estado] ?? {
    label: estado,
    className: "bg-gray-100 text-gray-800 border-gray-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        style.className,
      )}
    >
      {style.label}
    </span>
  );
}

// ── Drag-and-Drop instructional banner ─────────────────────────────────────

interface DragAndDropHintProps {
  equiposCount: number;
  participantesTotal: number;
}

function DragAndDropHint({
  equiposCount,
  participantesTotal,
}: DragAndDropHintProps) {
  const canMoveAcross = equiposCount > 1 && participantesTotal > 0;
  if (!canMoveAcross) {
    return null;
  }
  return (
    <div className="mb-4 flex items-start gap-3 rounded-2xl border border-violet-200/70 bg-gradient-to-r from-violet-50/80 via-sky-50/70 to-amber-50/70 p-3 shadow-sm">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-400 to-sky-500 text-white shadow-sm">
        <MousePointerClick className="size-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold uppercase tracking-wider text-violet-900 flex items-center gap-2">
          <span>Tip</span>
          <span className="text-[10px] font-medium text-violet-700/80 normal-case tracking-normal">
            — arrastrar y soltar
          </span>
        </p>
        <p className="mt-0.5 text-sm text-slate-700 leading-snug">
          Toca y mantén el ícono{" "}
          <GripVertical className="inline size-3 align-middle text-violet-600" />{" "}
          junto a un jugador para{" "}
          <span className="font-semibold text-violet-900">
            reordenarlo o moverlo a otro equipo
          </span>
          . El equipo destino se ilumina cuando es válido.
        </p>
      </div>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="shrink-0 rounded-full p-1.5 text-violet-700 hover:bg-violet-100 transition-colors"
            aria-label="Más información sobre arrastrar y soltar"
          >
            <Info className="size-4" />
          </button>
        </TooltipTrigger>
        <TooltipContent side="left" className="max-w-xs">
          <p className="font-semibold mb-1">¿Cómo funciona?</p>
          <ul className="text-xs space-y-1 leading-snug">
            <li>
              • Mantén el grip <span className="font-bold">⠿</span> y arrastra.
            </li>
            <li>• Suelta sobre otro equipo para mover al jugador.</li>
            <li>• Suelta en la misma lista para reordenar.</li>
            <li>• Si el destino ya tiene a esa persona, no se duplica.</li>
          </ul>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}

function PaymentCallout({
  estado,
  onOpenPayment,
}: {
  estado: string;
  onOpenPayment: () => void;
}) {
  const canContinuePayment = [
    "RECIBIDA",
    "PENDIENTE",
    "PAGO_PENDIENTE",
  ].includes(estado);
  const isIzipayEnabled = process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";
  if (!canContinuePayment || !isIzipayEnabled) return null;

  return (
    <section className="relative overflow-hidden rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 via-amber-50 to-rose-50 p-6 shadow-md sm:p-8">
      <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-amber-300/40 blur-2xl" />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
            <AlertCircle className="size-5" />
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-700">
              Pago pendiente
            </p>
            <h3 className="text-lg font-black tracking-tight text-amber-900">
              Completa el pago para procesar tu inscripcion
            </h3>
            <p className="max-w-xl text-sm leading-relaxed text-amber-900/80">
              Tu inscripcion esta guardando confirmacion de pago. Pagala con
              izipay para que el Comite Organizador la valide.
            </p>
          </div>
        </div>
        <Button
          type="button"
          onClick={onOpenPayment}
          className="btn-brand-gradient btn-shine h-12 rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg"
        >
          <CreditCard className="size-4" />
          Proceder al Pago
        </Button>
      </div>
    </section>
  );
}

function toBackendDraft(d: ParticipanteFormData) {
  return {
    tipoDocumento: d.tipoDocumento,
    numeroDocumento: d.numeroDocumento,
    nombres: d.nombres,
    apellidos: d.apellidos,
    genero: d.genero,
    telefono: d.telefono ?? null,
    whatsapp: d.whatsapp ?? null,
    rol: d.rol ?? "JUGADOR",
    talle_camiseta: d.talle_camiseta ?? null,
    notas: d.notas ?? null,
    acepto_bases: d.acepto_bases,
    acepto_aptitud_fisica: d.acepto_aptitud_fisica,
    acepto_imagen: d.acepto_imagen,
  };
}

export function InscripcionDetailView() {
  const params = useParams();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const inscripcionId = (params.id as string) ?? "";

  // ── Data: shared cache via TanStack Query ─────────────────────────────────
  // The query owns loading/error/data. Mutations update the same cache via
  // setQueryData so we don't refetch on every action.
  const {
    data: inscripcion,
    isLoading: loading,
    error: queryError,
  } = useInscripcionDetalle(inscripcionId);
  const error = queryError?.message ?? null;
  const cache = useInscripcionCacheSync(inscripcionId);

  const [addPanelEquipo, setAddPanelEquipo] = useState<EquipoItem | null>(null);
  const [addSelfEquipo, setAddSelfEquipo] = useState<EquipoItem | null>(null);
  const [equipoDrafts, setEquipoDrafts] = useState<
    Record<string, { drafts: DraftItem[]; saving: boolean }>
  >({});
  const [expandedEquipos, setExpandedEquipos] = useState<
    Record<string, boolean>
  >({});

  const [activeDragId, setActiveDragId] = useState<string | null>(null);

  // Editing state
  const [editingParticipante, setEditingParticipante] =
    useState<ParticipanteItem | null>(null);
  const [editingEquipo, setEditingEquipo] = useState<EquipoItem | null>(null);

  // Payment modal state
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);

  // Refs for in-page navigation
  const teamsSectionRef = useRef<HTMLDivElement | null>(null);

  const handleOpenPayment = useCallback(() => {
    setPaymentModalOpen(true);
  }, []);

  const handleScrollToTeams = useCallback(() => {
    teamsSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // When data first arrives, expand all teams by default.
  useEffect(() => {
    const current = inscripcion;
    if (!current) return;
    setExpandedEquipos((prev) => {
      if (Object.keys(prev).length > 0) return prev;
      return Object.fromEntries(
        current.equipos.map((e: EquipoItem) => [e.id, true]),
      );
    });
  }, [inscripcion]);

  // ── Drafts (working list per team) ───────────────────────────────────────
  function handleAddDraft(equipoId: string, data: ParticipanteFormData) {
    setEquipoDrafts((prev) => {
      const current = prev[equipoId] ?? { drafts: [], saving: false };
      return {
        ...prev,
        [equipoId]: {
          drafts: [
            ...current.drafts,
            { ...data, _key: `${Date.now()}-${Math.random()}` },
          ],
          saving: false,
        },
      };
    });
    setExpandedEquipos((prev) => ({ ...prev, [equipoId]: true }));
    setAddPanelEquipo(null);
  }

  function handleRemoveDraft(equipoId: string, key: string) {
    setEquipoDrafts((prev) => {
      const current = prev[equipoId];
      if (!current) return prev;
      return {
        ...prev,
        [equipoId]: {
          drafts: current.drafts.filter((d) => d._key !== key),
          saving: current.saving,
        },
      };
    });
  }

  async function saveEquipoDrafts(equipoId: string) {
    const drafts = equipoDrafts[equipoId]?.drafts ?? [];
    if (drafts.length === 0) return;
    setEquipoDrafts((prev) => ({
      ...prev,
      [equipoId]: { drafts: prev[equipoId]?.drafts ?? [], saving: true },
    }));
    try {
      const res = await agregarParticipantesAEquipo(inscripcionId, equipoId, {
        participantes: drafts.map(toBackendDraft),
      });
      if (!res.success || !res.data) {
        throw new Error(res.error?.message ?? "Error al guardar");
      }
      if (res.message) toast.success(res.message);
      // Backend now returns the canonical ParticipanteOut[] for each created
      // participante — append them to the cache in place (same shape as
      // InscripcionDetalleOut). No refetch needed.
      for (const participante of res.data.participantes) {
        cache.addParticipante(participante.equipo_id, participante);
      }
      setEquipoDrafts((prev) => ({
        ...prev,
        [equipoId]: { drafts: [], saving: false },
      }));
    } catch (e) {
      // Rollback on error.
      cache.invalidate();
      toast.error(
        e instanceof Error ? e.message : "Error al guardar jugadores",
      );
      setEquipoDrafts((prev) => ({
        ...prev,
        [equipoId]: {
          drafts: prev[equipoId]?.drafts ?? [],
          saving: false,
        },
      }));
    }
  }

  // ── Remove participant ────────────────────────────────────────────────────
  function handleRemoveParticipante(p: ParticipanteItem) {
    if (!confirm(`¿Eliminar a ${p.persona.nombres} ${p.persona.apellidos}?`))
      return;
    // Optimistic: remove from cache immediately.
    cache.removeParticipante(p.id);
    eliminarParticipante(inscripcionId, p.id)
      .then((res) => {
        if (!res.success || !res.data) {
          throw new Error(res.error?.message ?? "Error al eliminar");
        }
        if (res.message) toast.success(res.message);
      })
      .catch((e) => {
        // Roll back by re-invalidating.
        cache.invalidate();
        toast.error(
          e instanceof Error ? e.message : "Error al eliminar jugador",
        );
      });
  }

  // ── Add current user as participant ─────────────────────────────────────
  function handleYoClick(equipoId: string) {
    const eq = inscripcion?.equipos.find((e) => e.id === equipoId) ?? null;
    if (eq) setAddSelfEquipo(eq);
  }

  // ── Edit (open modal) ────────────────────────────────────────────────────
  function handleEditParticipante(p: ParticipanteItem, eq: EquipoItem) {
    setEditingParticipante(p);
    setEditingEquipo(eq);
  }

  // ── Drag & drop ─────────────────────────────────────────────────────────
  function handleDragStart(event: DragStartEvent) {
    setActiveDragId(String(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveDragId(null);
    if (!over || !inscripcion) return;

    const activeData = active.data.current as
      | { type: "participante"; equipoId: string }
      | undefined;
    if (!activeData || activeData.type !== "participante") return;

    const sourceEquipoId = activeData.equipoId;
    const participanteId = String(active.id);
    const overId = String(over.id);

    const equiposSnapshot: EquipoItem[] = inscripcion.equipos;
    let targetEquipoId: string | null = null;
    if (overId.startsWith("equipo-drop-")) {
      targetEquipoId = overId.replace("equipo-drop-", "");
    } else {
      for (const eq of equiposSnapshot) {
        if (eq.participantes.some((p: ParticipanteItem) => p.id === overId)) {
          targetEquipoId = eq.id;
          break;
        }
      }
    }

    if (!targetEquipoId || targetEquipoId === sourceEquipoId) return;

    // Optimistic move: update cache immediately, rollback on error.
    cache.moveParticipante(participanteId, targetEquipoId);
    moverParticipante(inscripcionId, participanteId, {
      equipo_destino_id: targetEquipoId,
    })
      .then((res) => {
        if (!res.success || !res.data) {
          throw new Error(res.error?.message ?? "Error al mover");
        }
      })
      .catch((e) => {
        cache.invalidate();
        toast.error(e instanceof Error ? e.message : "Error al mover jugador");
      });
  }

  const totalDrafts = useMemo(
    () =>
      Object.values(equipoDrafts).reduce(
        (sum: number, e: { drafts: DraftItem[]; saving: boolean }) =>
          sum + e.drafts.length,
        0,
      ),
    [equipoDrafts],
  );

  const equiposCount = inscripcion?.equipos.length ?? 0;
  const participantesTotal = useMemo(
    () =>
      inscripcion?.equipos.reduce(
        (acc: number, e: EquipoItem) => acc + e.participantes.length,
        0,
      ) ?? 0,
    [inscripcion],
  );

  return (
    <div className="flex min-h-svh w-full flex-col bg-[linear-gradient(180deg,#f6f4ee_0%,#ffffff_30%,#ffffff_100%)] text-slate-900">
      {/* Top bar */}
      <div className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/85 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-black uppercase tracking-wider text-[#312e8e] shadow-sm transition-colors hover:bg-slate-50"
          >
            <ArrowLeft className="size-4" />
            Volver
          </button>
          <div className="flex items-center gap-2">
            <span className="hidden text-[10px] font-black uppercase tracking-[0.2em] text-[#312e8e]/70 sm:inline">
              Detalle de Inscripcion
            </span>
          </div>
        </div>
      </div>

      <main className="mx-auto w-full max-w-5xl flex-1 space-y-8 px-4 py-8 sm:px-6 lg:px-10">
        {/* Hero with brand mark + estado + observacion (single source) */}
        {!loading && !error && inscripcion && (
          <section className="relative overflow-hidden rounded-3xl border border-slate-200/70 bg-gradient-to-br from-[#f6f4ee] via-white to-[#eef1f8] p-6 shadow-sm sm:p-8">
            <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-amber-300/30 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-12 -left-12 h-48 w-48 rounded-full bg-cyan-300/30 blur-3xl" />
            <div className="relative space-y-5">
              <div className="flex flex-col items-center gap-3 text-center">
                <p className="text-[10px] font-black uppercase tracking-[0.35em] text-[#312e8e]">
                  Inscripcion #{inscripcion.id.slice(0, 8)}
                </p>
                <FestBrandHeader
                  variant="onLight"
                  size="md"
                  eyebrow="Salesianos FEST 2026"
                />
                <p className="text-sm text-[#17214b]/70">
                  {inscripcion.evento.nombre} · creada el{" "}
                  {new Date(inscripcion.created_at).toLocaleDateString(
                    "es-PE",
                    {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    },
                  )}
                </p>
                {inscripcion && estadoBadge(inscripcion.estado)}
              </div>
              {inscripcion.observacion && (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-relaxed text-amber-900">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-700">
                    Observacion
                  </p>
                  <p className="mt-1">{inscripcion.observacion}</p>
                </div>
              )}
            </div>
          </section>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-[#17214b]/60">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-[#312e8e]" />
            <p className="text-xs uppercase tracking-wider text-[#17214b]/50">
              Cargando detalle...
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-center text-sm text-rose-700">
            {error}
          </div>
        )}

        {!loading && !error && inscripcion && (
          <>
            <RegistrationStepsCard
              inscripcion={inscripcion}
              onScrollToTeams={handleScrollToTeams}
              onOpenPayment={handleOpenPayment}
            />

            <PaymentCallout
              estado={inscripcion.estado}
              onOpenPayment={handleOpenPayment}
            />

            {/* Consolidated summary card */}
            <section className="overflow-hidden rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200/70 sm:p-8">
              <div className="pb-4">
                <h2 className="text-sm font-black uppercase tracking-wider text-slate-500">
                  Datos de la Inscripcion
                </h2>
              </div>
              <div className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
                {inscripcion.delegado && (
                  <SummaryItem
                    label="Delegado"
                    value={inscripcion.delegado.persona_nombre ?? "Sin nombre"}
                    secondary={
                      inscripcion.delegado.persona_numero_documento ?? null
                    }
                  />
                )}
                <SummaryItem
                  label="Fecha de inscripcion"
                  value={new Date(inscripcion.created_at).toLocaleDateString(
                    "es-PE",
                    {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    },
                  )}
                />
              </div>
              {inscripcion.observacion && (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm leading-relaxed text-amber-900">
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-700">
                    Observacion
                  </p>
                  <p className="mt-1">{inscripcion.observacion}</p>
                </div>
              )}
            </section>

            {/* Teams */}
            <div ref={teamsSectionRef}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-2">
                  <Users className="size-4" />
                  Equipos ({inscripcion.equipos.length})
                </h2>
                {totalDrafts > 0 && (
                  <span className="text-xs font-medium text-primary">
                    {totalDrafts} jugador{totalDrafts !== 1 ? "es" : ""}{" "}
                    pendiente{totalDrafts !== 1 ? "s" : ""} de guardar
                  </span>
                )}
              </div>

              {/* Drag-and-drop instructional banner */}
              <DragAndDropHint
                equiposCount={equiposCount}
                participantesTotal={participantesTotal}
              />

              {inscripcion.equipos.length > 0 ? (
                <DndContext
                  sensors={sensors}
                  collisionDetection={closestCorners}
                  onDragStart={handleDragStart}
                  onDragEnd={handleDragEnd}
                >
                  <div className="space-y-4">
                    {inscripcion.equipos.map((equipo: EquipoItem) => {
                      const draftState = equipoDrafts[equipo.id] ?? {
                        drafts: [],
                        saving: false,
                      };
                      const expanded = expandedEquipos[equipo.id] ?? true;

                      return (
                        <div key={equipo.id} className="space-y-2">
                          <SortableEquipoCard
                            equipo={equipo}
                            expanded={expanded}
                            onToggleExpand={() =>
                              setExpandedEquipos((prev) => ({
                                ...prev,
                                [equipo.id]: !expanded,
                              }))
                            }
                            onAddClick={() => setAddPanelEquipo(equipo)}
                            onYoClick={() => handleYoClick(equipo.id)}
                            onEditParticipante={(p) =>
                              handleEditParticipante(p, equipo)
                            }
                            onRemoveParticipante={handleRemoveParticipante}
                            activeDragId={activeDragId}
                          />

                          {draftState.drafts.length > 0 && (
                            <div className="ml-4 rounded-lg border border-dashed border-primary/40 bg-primary/5 p-3 space-y-2">
                              <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                                Jugadores por guardar (
                                {draftState.drafts.length})
                              </p>
                              <ul className="space-y-1">
                                {draftState.drafts.map((d) => (
                                  <li
                                    key={d._key}
                                    className="flex items-center justify-between gap-2 rounded-md border border-border/50 bg-background px-3 py-2 text-sm"
                                  >
                                    <div className="min-w-0">
                                      <div className="flex items-center gap-1.5">
                                        <p className="font-medium truncate">
                                          {d.nombres} {d.apellidos}
                                        </p>
                                        {d.notas?.trim() && (
                                          <span
                                            className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-1.5 py-0.5 text-[10px] font-semibold text-violet-700 shrink-0"
                                            title="Tiene notas internas"
                                          >
                                            <MessageSquare className="size-2.5" />
                                            Nota
                                          </span>
                                        )}
                                      </div>
                                      <p className="text-xs text-muted-foreground">
                                        {d.tipoDocumento} {d.numeroDocumento} •{" "}
                                        {d.talle_camiseta ?? "Sin talle"} •{" "}
                                        {d.rol ?? "JUGADOR"}
                                      </p>
                                    </div>
                                    <button
                                      type="button"
                                      onClick={() =>
                                        handleRemoveDraft(equipo.id, d._key)
                                      }
                                      className="text-xs text-muted-foreground hover:text-destructive shrink-0"
                                      aria-label="Quitar de la lista"
                                    >
                                      Quitar
                                    </button>
                                  </li>
                                ))}
                              </ul>
                              <button
                                type="button"
                                onClick={() => saveEquipoDrafts(equipo.id)}
                                disabled={draftState.saving}
                                className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm font-semibold hover:bg-primary/90 disabled:opacity-50"
                              >
                                <Save className="size-4" />
                                {draftState.saving
                                  ? "Guardando..."
                                  : `Guardar ${draftState.drafts.length} jugador${draftState.drafts.length !== 1 ? "es" : ""}`}
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <DragOverlay>
                    {activeDragId ? (
                      <div className="rounded-md border-2 border-primary bg-card px-3 py-2 shadow-xl">
                        <p className="text-sm font-semibold">
                          Moviendo jugador…
                        </p>
                      </div>
                    ) : null}
                  </DragOverlay>
                </DndContext>
              ) : (
                <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
                  <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-amber-50 text-amber-600">
                    <Package className="size-5" />
                  </div>
                  <p className="text-sm font-medium text-gray-700">
                    Esta inscripción aún no tiene equipos.
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Crea la inscripción desde el wizard para agregar equipos.
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {addPanelEquipo && (
        <AddParticipanteModal
          equipoId={addPanelEquipo.id}
          open={!!addPanelEquipo}
          onOpenChange={(o) => {
            if (!o) setAddPanelEquipo(null);
          }}
          equipoLabel={`${addPanelEquipo.nombre} (${addPanelEquipo.disciplina.nombre})`}
          onAdd={(data) => handleAddDraft(addPanelEquipo.id, data)}
        />
      )}

      {editingParticipante && editingEquipo && (
        <EditParticipanteModal
          open={!!editingParticipante}
          onOpenChange={(o) => {
            if (!o) {
              setEditingParticipante(null);
              setEditingEquipo(null);
            }
          }}
          inscripcionId={inscripcionId}
          participante={editingParticipante}
          equipoLabel={`${editingEquipo.nombre} (${editingEquipo.disciplina.nombre})`}
          onSuccess={cache.invalidate}
        />
      )}

      {addSelfEquipo && (
        <AgregarmeModal
          open={!!addSelfEquipo}
          onOpenChange={(o) => {
            if (!o) setAddSelfEquipo(null);
          }}
          inscripcionId={inscripcionId}
          equipoId={addSelfEquipo.id}
          equipoLabel={`${addSelfEquipo.nombre} (${addSelfEquipo.disciplina.nombre})`}
          personaId={user?.persona_id ?? null}
          user={{
            nombres: user?.nombres ?? null,
            apellidos: user?.apellidos ?? null,
            email: user?.email ?? null,
          }}
          onSuccess={cache.invalidate}
        />
      )}

      <IzipayModal
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        inscripcionId={inscripcionId}
        onSuccess={cache.invalidate}
      />
    </div>
  );
}
