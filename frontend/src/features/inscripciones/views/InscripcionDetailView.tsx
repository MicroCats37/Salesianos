"use client";

import { ArrowLeft, Users } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { IzipayModal } from "@/features/pagos";
import { AddParticipanteModal } from "../components/AddParticipanteModal";
import { DatosInscripcionCard } from "../components/DatosInscripcionCard";
import { EditParticipanteModal } from "../components/EditParticipanteModal";
import { EquipoCard } from "../components/EquipoCard";
import { EquiposEmptyState } from "../components/EquiposEmptyState";
import { EstadoProgresoCard } from "../components/EstadoProgresoCard";
import { InscripcionErrorState } from "../components/InscripcionErrorState";
import { InscripcionHero } from "../components/InscripcionHero";
import { InscripcionSkeleton } from "../components/InscripcionSkeleton";
import { PaymentCallout } from "../components/PaymentCallout";
import {
  type ParticipanteColocado,
  PoolParticipantesSeccion,
} from "../components/PoolParticipantesSeccion";
import { ResumenPagoCard } from "../components/ResumenPagoCard";
import { SelectorParticipanteModal } from "../components/SelectorParticipanteModal";
import { useElegiblesEquipos } from "../hooks/useElegiblesEquipo";
import { useInscripcionCacheSync } from "../hooks/useInscripcionCacheSync";
import { useInscripcionDetalle } from "../hooks/useInscripcionDetalle";
import {
  useInscripcionPool,
  useInscripcionSaldo,
} from "../hooks/useInscripcionPool";
import { usePreregistrarEnPool } from "../hooks/usePreregistrarEnPool";
import type { ParticipanteFormData } from "../schemas/participante.schema";
import {
  eliminarParticipante,
  type InscripcionDetalleOut,
} from "../services/inscripcion.service";
import { compraPagableId } from "../utils/pago.estado";
import {
  buildPreregistroPayload,
  buildPreregistroSelfPayload,
} from "../utils/pool.preregistro";

type EquipoItem = InscripcionDetalleOut["equipos"][number];
type ParticipanteItem = EquipoItem["participantes"][number];

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
    isFetching,
    error: queryError,
    refetch,
  } = useInscripcionDetalle(inscripcionId);
  const error = queryError?.message ?? null;
  const cache = useInscripcionCacheSync(inscripcionId);

  // ── Participant pool ─────────────────────────────────────────────────────
  // The pool endpoint is the only source of eligibility: the backend
  // decides who has a paid cup and why the others are blocked.
  const {
    data: poolData,
    isLoading: poolLoading,
    error: poolError,
  } = useInscripcionPool(inscripcionId);
  const { data: saldo } = useInscripcionSaldo(inscripcionId);
  const preregistrarPool = usePreregistrarEnPool(inscripcionId);
  const poolEntries = poolData?.pool ?? [];

  // Pool preregistration modal — the participant joins the pool with no team.
  const [addPoolOpen, setAddPoolOpen] = useState(false);

  /**
   * Participant selector — the assignment gesture.
   *
   * `selectorEquipo` is the target team; `selectorCandidatoId` preselects a
   * person (e.g. from the pool card "Asignar" button).
   */
  const [selectorEquipo, setSelectorEquipo] = useState<EquipoItem | null>(null);
  const [selectorCandidatoId, setSelectorCandidatoId] = useState<string | null>(
    null,
  );

  const [expandedEquipos, setExpandedEquipos] = useState<
    Record<string, boolean>
  >({});

  /** Opens the selector for a team, optionally preselecting a candidate. */
  function handleOpenSelector(equipo: EquipoItem, candidatoId?: string | null) {
    setSelectorEquipo(equipo);
    setSelectorCandidatoId(candidatoId ?? null);
  }

  // Editing state
  const [editingParticipante, setEditingParticipante] =
    useState<ParticipanteItem | null>(null);
  const [editingEquipo, setEditingEquipo] = useState<EquipoItem | null>(null);

  // Payment modal state
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  /**
   * The purchase the checkout pays. It is derived from the commercial summary:
   * a purchase is payable while it is PENDIENTE and its payment order has not
   * been paid yet.
   */
  const compraPendienteId = compraPagableId(inscripcion?.resumen_pago);

  // Refs for in-page navigation
  const teamsSectionRef = useRef<HTMLDivElement | null>(null);

  const handleOpenPayment = useCallback(() => {
    if (!compraPendienteId) {
      toast.info("No hay compras pendientes de pago.");
      return;
    }
    setPaymentModalOpen(true);
  }, [compraPendienteId]);

  const handleScrollToTeams = useCallback(() => {
    teamsSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, []);

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

  // ── Pool preregistration ────────────────────────────────────────────────
  // The backend owns the capacity and deadline rules: on rejection the
  // mutation surfaces its message and nothing is invalidated.
  async function handleAddToPool(data: ParticipanteFormData) {
    await preregistrarPool.mutateAsync(buildPreregistroPayload(data));
  }

  /**
   * Pool-first self registration of the responsable.
   *
   * The person is preregistered in the POOL (no `equipo_id`): the team
   * placement is a later step done with the selector. There is no direct
   * "add me to this team" shortcut anymore.
   */
  async function handleAgregarmeAlPool() {
    const personaId = user?.persona_id ?? null;
    if (!personaId) {
      toast.error(
        "No tienes una persona asociada. Completa tu registro primero.",
      );
      return;
    }
    await preregistrarPool.mutateAsync(buildPreregistroSelfPayload(personaId));
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

  // ── Edit (open modal) ────────────────────────────────────────────────────
  function handleEditParticipante(p: ParticipanteItem, eq: EquipoItem) {
    setEditingParticipante(p);
    setEditingEquipo(eq);
  }

  const equiposCount = inscripcion?.equipos.length ?? 0;

  /**
   * Candidate list of every team, prefetched.
   *
   * Two things need it BEFORE the modal opens: the team card must know
   * whether somebody can be added (otherwise the button opens an empty
   * selector), and the pool needs to know in which team a person IS
   * assignable. One cup authorises a person in every contracted discipline,
   * so the teams share candidates.
   */
  const elegiblesPorEquipo = useElegiblesEquipos(
    inscripcionId,
    useMemo(
      () => (inscripcion?.equipos ?? []).map((equipo) => equipo.id),
      [inscripcion?.equipos],
    ),
  );

  /** How many people the backend reports as assignable to each team. */
  const asignablesPorEquipo = useMemo(() => {
    const mapa = new Map<string, number>();
    for (const equipo of elegiblesPorEquipo) {
      const asignables =
        equipo.data?.elegibles.filter((candidato) => candidato.asignable)
          .length ?? 0;
      mapa.set(equipo.equipoId, asignables);
    }
    return mapa;
  }, [elegiblesPorEquipo]);

  /** Whether the backend says the person can join that team right now. */
  const esAsignableEnEquipo = useCallback(
    (equipoId: string, inscripcionPersonaId: string) => {
      const equipo = elegiblesPorEquipo.find(
        (item) => item.equipoId === equipoId,
      );
      const candidato = equipo?.data?.elegibles.find(
        (item) => item.id === inscripcionPersonaId,
      );
      return candidato?.asignable === true;
    },
    [elegiblesPorEquipo],
  );

  /**
   * The responsable is already in the pool: offering "Agregarme al pool"
   * again is a dead action that only confuses.
   */
  const responsableEnPool = useMemo(
    () =>
      !!user?.persona_id &&
      poolEntries.some((entrada) => entrada.persona.id === user?.persona_id),
    [poolEntries, user?.persona_id],
  );

  /**
   * People already sitting in a team.
   *
   * The pool endpoint excludes them by design (it only returns people without
   * an active participacion), so the roster is the only source for the
   * "already placed" state.
   *
   * One entry per ROSTER ROW: a person that plays in two disciplines appears
   * twice — once per team — and each row is keyed by its `Participacion.id`.
   */
  const colocados = useMemo<ParticipanteColocado[]>(() => {
    if (!inscripcion) return [];
    const list: ParticipanteColocado[] = [];
    for (const eq of inscripcion.equipos) {
      for (const p of eq.participantes) {
        if (p.estado !== "A" || !p.persona) continue;
        list.push({
          participacionId: p.id,
          inscripcionPersonaId: p.inscripcion_persona_id,
          nombre: p.persona.nombre,
          equipoNombre: p.equipo_nombre || eq.nombre,
          disciplinaSigla: p.disciplina?.sigla ?? eq.disciplina?.sigla ?? null,
        });
      }
    }
    return list;
  }, [inscripcion]);

  return (
    <div className="surface-page-gradient flex min-h-svh w-full flex-col text-slate-900">
      {/* Top bar */}
      <div className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/85 px-4 py-3 backdrop-blur sm:px-6">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 text-xs font-black uppercase tracking-wider text-[#312e8e] shadow-sm transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#312e8e] focus-visible:ring-offset-2"
          >
            <ArrowLeft className="size-4" />
            Volver
          </button>
          <div className="flex items-center gap-2">
            <span className="hidden text-[10px] font-black uppercase tracking-[0.2em] text-[#312e8e]/70 sm:inline">
              Detalle de inscripcion
            </span>
          </div>
        </div>
      </div>

      {loading && <InscripcionSkeleton />}

      {!loading && (error || !inscripcion) && (
        <InscripcionErrorState
          message={error ?? "No se encontro la inscripcion solicitada."}
          retrying={isFetching}
          onRetry={() => {
            void refetch();
          }}
        />
      )}

      {!loading && !error && inscripcion && (
        <>
          <InscripcionHero inscripcion={inscripcion} />

          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
            <div className="flex flex-col gap-6 xl:grid xl:grid-cols-12 xl:gap-8">
              {/* ── Operational content ── */}
              <div className="order-1 min-w-0 space-y-8 xl:col-span-8">
                {/* The ONE place that shows the state and the progress of the
                    inscription: badge, meaning, one progress bar and one
                    checklist. */}
                <EstadoProgresoCard
                  inscripcion={inscripcion}
                  onScrollToTeams={handleScrollToTeams}
                />

                {/* The ONE payment action of the page. */}
                <PaymentCallout
                  resumenPago={inscripcion.resumen_pago}
                  estado={inscripcion.estado}
                  onOpenPayment={handleOpenPayment}
                />

                {/* Participant pool — pre-registered people. Eligibility comes
                    from the backend, never from a local computation. */}
                <PoolParticipantesSeccion
                  pool={poolEntries}
                  loading={poolLoading}
                  error={poolError?.message ?? null}
                  colocados={colocados}
                  saldo={saldo ?? null}
                  resumenPago={inscripcion.resumen_pago}
                  inscripcionEstado={inscripcion.estado}
                  equiposCount={equiposCount}
                  equipos={inscripcion.equipos}
                  onAddParticipant={() => setAddPoolOpen(true)}
                  onAgregarme={
                    responsableEnPool ? undefined : handleAgregarmeAlPool
                  }
                  personaResponsableId={user?.persona_id ?? null}
                  agregarmeLoading={preregistrarPool.isPending}
                  onAsignar={(inscripcionPersonaId) => {
                    // The pool card does not know the team: open the selector of
                    // the FIRST team where the person is ASSIGNABLE. Opening a
                    // team where the backend says "no" would show the person
                    // preselected and disabled.
                    const equipo =
                      inscripcion.equipos.find((item) =>
                        esAsignableEnEquipo(item.id, inscripcionPersonaId),
                      ) ?? inscripcion.equipos[0];
                    if (!equipo) return;
                    handleOpenSelector(equipo, inscripcionPersonaId);
                  }}
                />

                {/* Teams */}
                <section
                  id="equipos"
                  ref={teamsSectionRef}
                  className="scroll-mt-24 space-y-4"
                  aria-labelledby="equipos-titulo"
                >
                  <header className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
                        Delegacion
                      </p>
                      <h2
                        id="equipos-titulo"
                        className="mt-1 flex items-center gap-2 text-xl font-black tracking-tight text-[#17214b] sm:text-2xl"
                      >
                        <Users className="size-5" />
                        Equipos ({inscripcion.equipos.length})
                      </h2>
                    </div>
                  </header>

                  {inscripcion.equipos.length > 0 ? (
                    <div className="space-y-4">
                      {inscripcion.equipos.map((equipo: EquipoItem) => {
                        const expanded = expandedEquipos[equipo.id] ?? true;

                        return (
                          <EquipoCard
                            key={equipo.id}
                            equipo={equipo}
                            expanded={expanded}
                            onToggleExpand={() =>
                              setExpandedEquipos((prev) => ({
                                ...prev,
                                [equipo.id]: !expanded,
                              }))
                            }
                            onAsignarClick={() => handleOpenSelector(equipo)}
                            asignables={asignablesPorEquipo.get(equipo.id)}
                            onEditParticipante={(p) =>
                              handleEditParticipante(p, equipo)
                            }
                            onRemoveParticipante={handleRemoveParticipante}
                          />
                        );
                      })}
                    </div>
                  ) : (
                    <EquiposEmptyState
                      onVolver={() => router.push("/dashboard")}
                    />
                  )}
                </section>
              </div>

              {/* ── Reference column: money + people ── */}
              <aside
                aria-labelledby="resumen-inscripcion-titulo"
                className="order-2 space-y-4 xl:col-span-4 xl:self-start xl:sticky xl:top-24 xl:z-20"
              >
                <h2 id="resumen-inscripcion-titulo" className="sr-only">
                  Resumen de la inscripcion
                </h2>

                {/* Aggregate commercial / payment summary — presenter-derived, read-only */}
                <ResumenPagoCard
                  resumen={inscripcion.resumen_pago}
                  variant="compact"
                />

                <DatosInscripcionCard inscripcion={inscripcion} />
              </aside>
            </div>
          </main>
        </>
      )}

      {selectorEquipo && (
        <SelectorParticipanteModal
          open={!!selectorEquipo}
          onOpenChange={(o) => {
            if (!o) {
              setSelectorEquipo(null);
              setSelectorCandidatoId(null);
            }
          }}
          inscripcionId={inscripcionId}
          equipos={inscripcion?.equipos ?? []}
          equipoInicialId={selectorEquipo.id}
          candidatoInicialId={selectorCandidatoId}
        />
      )}

      {addPoolOpen && (
        <AddParticipanteModal
          open={addPoolOpen}
          onOpenChange={(o) => {
            if (!o) setAddPoolOpen(false);
          }}
          primaryLoading={preregistrarPool.isPending}
          onAdd={handleAddToPool}
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

      <IzipayModal
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        compraId={compraPendienteId}
        onSuccess={cache.invalidate}
      />
    </div>
  );
}
