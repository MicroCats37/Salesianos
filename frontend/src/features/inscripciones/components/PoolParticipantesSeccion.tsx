"use client";

import {
  AlertCircle,
  Clock,
  CreditCard,
  Layers,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type {
  InscripcionDetalleOut,
  ResumenPagoOut,
} from "../services/inscripcion.service";
import type { PoolEntryOut, SaldoOut } from "../services/pool.service";
import {
  compraPagable,
  activacionPendiente as hayActivacionPendiente,
  pagoBloqueadoPorEstado,
} from "../utils/pago.estado";
import { poolEstadoDeEntrada } from "../utils/pool.estado";
import { poolCtaDe } from "../utils/pool.primero";
import {
  ParticipanteColocadoRow,
  PoolParticipanteCard,
} from "./PoolParticipanteCard";

type EquipoItem = InscripcionDetalleOut["equipos"][number];

/** A pre-registered participant that already sits in a team. */
export interface ParticipanteColocado {
  /**
   * `Participacion.id` — unique per roster row.
   *
   * It is the React key of the row: one person can play in SEVERAL disciplines
   * (one paid cup), so keying by the person would duplicate the key.
   */
  participacionId: string;
  /** `InscripcionPersona.id` — the person (shared across disciplines). */
  inscripcionPersonaId: string;
  /** Full name of the person. */
  nombre: string;
  /** Team where the person is placed. */
  equipoNombre: string;
  /** Sigla of the discipline of that team. */
  disciplinaSigla: string | null;
}

export interface PoolParticipantesSeccionProps {
  /** Pool entries from `GET /inscripciones/{id}/pool`. */
  pool: PoolEntryOut[];
  /** Pool query state. */
  loading: boolean;
  /** Pool query error (already user-facing). */
  error: string | null;
  /** People already sitting in a team (active `Participacion`). */
  colocados: ParticipanteColocado[];
  /** Cupo saldo — `null` when it could not be loaded. */
  saldo: SaldoOut | null;
  /** Commercial summary — presenter-derived, read-only. */
  resumenPago: ResumenPagoOut;
  /**
   * Inscription administrative state. It never describes the commercial
   * state: it only vetoes the payment when the inscription was cancelled or
   * rejected (same rule as the payment callout).
   */
  inscripcionEstado: string;
  /** Number of teams available as assignment targets. */
  equiposCount: number;
  /**
   * Teams of the inscription. Used only to report how many players each team
   * still needs — the counters come from the backend presenter
   * (`EquipoDetalleOut.faltantes`), never from a local computation.
   */
  equipos?: EquipoItem[];
  /** Opens the preregistration modal (pool mode, no team). */
  onAddParticipant: () => void;
  /**
   * Opens the payment modal.
   */
  onOpenPayment: () => void;
  /**
   * Preregisters the RESPONSIBLE in the pool (pool-first self registration).
   *
   * It never places anybody in a team: the team placement is done afterwards
   * with the selector.
   */
  onAgregarme?: () => void;
  /** `persona_id` of the authenticated user — `null` when it is unknown. */
  personaResponsableId?: string | null;
  /** Loading state of the self registration. */
  agregarmeLoading?: boolean;
  /**
   * Opens the participant selector with the given person preselected.
   * When it is not provided the pool cards are read-only.
   */
  onAsignar?: (inscripcionPersonaId: string) => void;
}

/**
 * Participant pool section of the inscription detail.
 *
 * It renders what the backend returned — never a locally computed eligibility:
 * the pool endpoint decides `tiene_cupo_activo` and `motivo_bloqueo`, and the
 * saldo endpoint decides whether paid capacity is left.
 */
export function PoolParticipantesSeccion({
  pool,
  loading,
  error,
  colocados,
  saldo,
  resumenPago,
  inscripcionEstado,
  equiposCount,
  equipos = [],
  onAddParticipant,
  onOpenPayment,
  onAgregarme,
  personaResponsableId,
  agregarmeLoading = false,
  onAsignar,
}: PoolParticipantesSeccionProps) {
  const isIzipayEnabled = process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";

  // The payment action is a COMMERCIAL decision: it is offered when the
  // commercial summary reports a payable purchase. The administrative state is
  // only used to veto a cancelled/rejected inscription.
  const bloqueadoPorEstado = pagoBloqueadoPorEstado(inscripcionEstado);
  const hayCompraPagable = compraPagable(resumenPago) !== null;
  const puedePagar = hayCompraPagable && !bloqueadoPorEstado && isIzipayEnabled;

  /**
   * People vs roster rows.
   *
   * One paid cup authorises a person in EVERY contracted discipline, so the
   * roster holds MORE rows than there are people. The header counts the
   * distinct people (comparable with the paid cupos); the "Ya asignados"
   * block counts the roster rows (participaciones).
   */
  const personasColocadas = new Set(
    colocados.map((colocado) => colocado.inscripcionPersonaId),
  ).size;
  const totalPersonas = pool.length + personasColocadas;

  // Missing players per team — presenter counters, not a local computation.
  const equiposIncompletos = equipos.filter((equipo) => equipo.faltantes > 0);
  const faltantesTotal = equiposIncompletos.reduce(
    (acc, equipo) => acc + equipo.faltantes,
    0,
  );

  const bloqueados = pool.filter((entry) => !entry.tiene_cupo_activo);
  // Participants whose payment already exists and whose cup is simply not
  // assigned yet — they are NOT waiting for a payment, so the payment CTA
  // must not be offered for them.
  const porAsignar = bloqueados.filter(
    (entry) => poolEstadoDeEntrada(entry) === "cupo_por_asignar",
  ).length;
  const sinCapacidadPagada = saldo !== null && saldo.disponibles_pagados === 0;
  const hayPagosPendientes = resumenPago.compras_pendientes > 0;
  // The payment is recorded but the rights are not allocated yet.
  const activacionPendiente = hayActivacionPendiente(resumenPago);

  // The contextual callout is derived from the returned pool/saldo fields:
  // a participant whose cup is simply not assigned yet never gets a payment
  // CTA (the payment already exists).
  const cta =
    !loading && !error && bloqueados.length > 0 ? (
      porAsignar > 0 ? (
        <CupoPorAsignarCallout />
      ) : sinCapacidadPagada ? (
        activacionPendiente ? (
          <ActivacionPendienteCallout />
        ) : hayPagosPendientes ? (
          <PagarCallout
            bloqueados={bloqueados.length}
            puedePagar={puedePagar}
            motivoBloqueo={
              bloqueadoPorEstado
                ? "Esta inscripcion esta cancelada o rechazada."
                : "El pago en linea no esta disponible en este momento."
            }
            onOpenPayment={onOpenPayment}
          />
        ) : (
          <AmpliarCallout bloqueados={bloqueados.length} />
        )
      ) : null
    ) : null;

  return (
    <section className="space-y-4" aria-labelledby="pool-participantes-titulo">
      {/* ── Header ── */}
      <header className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
              Participantes
            </p>
            <h2
              id="pool-participantes-titulo"
              className="mt-1 text-xl font-black tracking-tight text-[#17214b] sm:text-2xl"
            >
              Pool de participantes
            </h2>
          </div>

          {/* The pool is the ONLY entry point of the participant lifecycle:
              the CTA is full width on mobile so it never competes with the
              saldo chips. */}
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
            <Button
              type="button"
              onClick={onAddParticipant}
              className="btn-brand-gradient btn-shine h-11 w-full gap-1.5 rounded-full px-4 text-xs font-black uppercase tracking-widest shadow-sm sm:w-auto"
            >
              <UserPlus className="size-4" />
              {poolCtaDe("cabecera").label}
            </Button>
            {onAgregarme && personaResponsableId && (
              <button
                type="button"
                onClick={onAgregarme}
                disabled={agregarmeLoading}
                className="inline-flex h-11 items-center gap-1.5 rounded-full px-2 text-xs font-bold uppercase tracking-wider text-primary underline underline-offset-4 transition-colors hover:text-primary/80 disabled:opacity-60"
              >
                <UserPlus className="size-4" />
                {agregarmeLoading ? "Agregando..." : "Agregarme al pool"}
              </button>
            )}
          </div>
        </div>

        <p className="mt-3 max-w-3xl text-xs leading-relaxed text-slate-600 sm:text-sm">
          Las personas pre-registradas quedan aqui hasta que se asignan a un
          equipo. Solo pueden unirse a un equipo cuando tienen un cupo pagado
          asignado. Registrar y asignar son dos pasos: primero el pool, despues
          el selector del equipo.
        </p>

        {/* ── At a glance ── */}
        <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
          <StatTile
            icon={Users}
            label="En el pool"
            value={pool.length}
            hint={`${totalPersonas} personas en total`}
          />
          <StatTile
            icon={UserCheck}
            label="Asignadas"
            value={personasColocadas}
            hint={`${colocados.length} participaciones`}
          />
          <StatTile
            icon={AlertCircle}
            label="Faltan por equipo"
            value={faltantesTotal}
            tone={faltantesTotal > 0 ? "amber" : "emerald"}
            hint={
              faltantesTotal > 0
                ? `${equiposIncompletos.length} equipo(s) por completar`
                : "Todos los equipos completos"
            }
          />
          <StatTile
            icon={CreditCard}
            label="Cupos pagados"
            value={saldo?.pagados ?? 0}
            tone={(saldo?.disponibles_pagados ?? 0) > 0 ? "brand" : "neutral"}
            hint={
              saldo
                ? `${saldo.asignados_pagados} asignados · ${saldo.disponibles_pagados} disponibles`
                : "Sin datos de saldo"
            }
          />
        </div>

        {/* ── Paid capacity balance ── */}
        {saldo && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <SaldoChip label="Lugares contratados" value={saldo.contratados} />
            <SaldoChip
              label="Cupos asignados"
              value={saldo.asignados_pagados}
            />
            <SaldoChip
              label="Disponibles"
              value={saldo.disponibles_pagados}
              highlight={saldo.disponibles_pagados > 0}
            />
          </div>
        )}

        {/* ── Teams that still need players ── */}
        {equiposIncompletos.length > 0 && (
          <p className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-2xl bg-amber-50/70 px-3 py-2.5 text-xs text-amber-900">
            <span className="font-black uppercase tracking-wider text-amber-700">
              Faltan jugadores en
            </span>
            {equiposIncompletos.map((equipo) => (
              <span
                key={equipo.id}
                className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-white px-2 py-0.5 font-semibold"
              >
                {equipo.nombre}
                <span className="tabular-nums text-amber-700">
                  ({equipo.faltantes})
                </span>
              </span>
            ))}
          </p>
        )}
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
        >
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-4 text-xs text-slate-500">
          <span className="size-4 animate-spin rounded-full border-2 border-slate-200 border-t-[#312e8e]" />
          Cargando pool de participantes...
        </div>
      )}

      {!loading && !error && pool.length === 0 && colocados.length === 0 && (
        <div className="relative overflow-hidden rounded-3xl border border-dashed border-sky-300 bg-gradient-to-br from-sky-50 via-white to-indigo-50 p-8 text-center shadow-sm">
          <div className="pointer-events-none absolute -right-12 -top-12 size-40 rounded-full bg-sky-200/40 blur-3xl" />
          <div className="relative mx-auto max-w-md space-y-4">
            <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-indigo-600 text-white shadow-lg">
              <Users className="size-6" />
            </span>
            <div className="space-y-1.5">
              <h3 className="text-lg font-black tracking-tight text-slate-900">
                Sin participantes pre-registrados
              </h3>
              <p className="text-sm leading-relaxed text-slate-600">
                {poolCtaDe("vacio").description}
              </p>
            </div>
            <Button
              type="button"
              onClick={onAddParticipant}
              className="btn-brand-gradient btn-shine h-12 w-full gap-1.5 rounded-full px-5 text-xs font-black uppercase tracking-widest shadow-lg sm:w-auto"
            >
              <UserPlus className="size-4" />
              {poolCtaDe("vacio").label}
            </Button>
          </div>
        </div>
      )}

      {/* ── Actionable pool entries ── */}
      {!loading && !error && pool.length > 0 && (
        <ul className="space-y-2">
          {pool.map((entry) => (
            <li key={entry.id}>
              <PoolParticipanteCard
                entry={entry}
                sinDestino={equiposCount === 0}
                onAsignar={onAsignar}
              />
            </li>
          ))}
        </ul>
      )}

      {/* ── People already placed in a team ── */}
      {!loading && !error && colocados.length > 0 && (
        <details className="rounded-3xl border border-slate-200 bg-white shadow-sm">
          <summary className="cursor-pointer px-5 py-4 text-xs font-black uppercase tracking-wider text-slate-500">
            Ya asignados ({colocados.length} participaciones ·{" "}
            {personasColocadas} personas)
          </summary>
          <ul className="space-y-2 border-t border-slate-100 p-3">
            {colocados.map((colocado) => (
              <li key={colocado.participacionId}>
                <ParticipanteColocadoRow
                  nombre={colocado.nombre}
                  equipoNombre={colocado.equipoNombre}
                  disciplinaSigla={colocado.disciplinaSigla}
                />
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* ── Context CTA — derived from the returned pool/saldo fields ── */}
      {cta}
    </section>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

type StatTone = "neutral" | "brand" | "amber" | "emerald";

interface StatTileProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  hint?: string;
  tone?: StatTone;
}

const TONE_CLASSES: Record<
  StatTone,
  { surface: string; icon: string; value: string }
> = {
  neutral: {
    surface: "bg-slate-50",
    icon: "bg-white text-slate-500",
    value: "text-slate-900",
  },
  brand: {
    surface: "bg-[#312e8e]/10",
    icon: "bg-white text-[#312e8e]",
    value: "text-[#17214b]",
  },
  amber: {
    surface: "bg-amber-50",
    icon: "bg-white text-amber-600",
    value: "text-amber-900",
  },
  emerald: {
    surface: "bg-emerald-50",
    icon: "bg-white text-emerald-600",
    value: "text-emerald-900",
  },
};

function StatTile({
  icon: Icon,
  label,
  value,
  hint,
  tone = "neutral",
}: StatTileProps) {
  const classes = TONE_CLASSES[tone];

  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/70 p-3",
        classes.surface,
      )}
    >
      <div className="flex items-start gap-2">
        <span
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-lg shadow-sm",
            classes.icon,
          )}
        >
          <Icon className="size-3.5" />
        </span>
        <p className="min-w-0 text-[10px] font-black uppercase leading-tight tracking-[0.15em] text-slate-500">
          {label}
        </p>
      </div>
      <p
        className={cn(
          "mt-2 text-2xl font-black leading-none tabular-nums",
          classes.value,
        )}
      >
        {value}
      </p>
      {hint && (
        <p className="mt-1 text-xs leading-snug text-slate-500">{hint}</p>
      )}
    </div>
  );
}

function SaldoChip({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        highlight
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-slate-200 bg-slate-50 text-slate-600",
      )}
      title={`${label}: ${value}`}
    >
      {label}
      <span className="tabular-nums">{value}</span>
    </span>
  );
}

function PagarCallout({
  bloqueados,
  puedePagar,
  motivoBloqueo,
  onOpenPayment,
}: {
  bloqueados: number;
  puedePagar: boolean;
  motivoBloqueo: string;
  onOpenPayment: () => void;
}) {
  return (
    <div
      aria-live="polite"
      className="relative overflow-hidden rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 via-amber-50 to-rose-50 p-5 shadow-md sm:p-6"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
            <AlertCircle className="size-5" />
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-700">
              Pago pendiente
            </p>
            <h3 className="text-lg font-black tracking-tight text-amber-900">
              Completa el pago para liberar {bloqueados}{" "}
              {bloqueados === 1 ? "participante" : "participantes"}
            </h3>
            <p className="max-w-xl text-sm leading-relaxed text-amber-900/80">
              No hay cupos pagados disponibles. Al confirmar el pago pendiente
              se asignan los cupos y los participantes bloqueados podran unirse
              a un equipo.
            </p>
          </div>
        </div>
        {puedePagar ? (
          <Button
            type="button"
            onClick={onOpenPayment}
            className="btn-brand-gradient btn-shine h-12 shrink-0 rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg"
          >
            <CreditCard className="size-4" />
            Proceder al Pago
          </Button>
        ) : (
          <p className="max-w-xs text-xs leading-relaxed text-amber-900/70">
            {motivoBloqueo}
          </p>
        )}
      </div>
    </div>
  );
}

function ActivacionPendienteCallout() {
  return (
    <div
      aria-live="polite"
      className="relative overflow-hidden rounded-3xl border border-amber-200 bg-gradient-to-r from-amber-50 via-amber-50 to-rose-50 p-5 shadow-md sm:p-6"
    >
      <div className="flex items-start gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
          <Clock className="size-5" />
        </div>
        <div className="space-y-1">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-700">
            Activacion pendiente
          </p>
          <h3 className="text-lg font-black tracking-tight text-amber-900">
            Tu pago esta registrado
          </h3>
          <p className="max-w-xl text-sm leading-relaxed text-amber-900/80">
            El Comite Organizador ya recibio tu pago y esta habilitando los
            cupos. En cuanto termine, los participantes bloqueados podran unirse
            a un equipo. No vuelvas a pagar.
          </p>
        </div>
      </div>
    </div>
  );
}

function CupoPorAsignarCallout() {
  return (
    <div
      aria-live="polite"
      className="relative overflow-hidden rounded-3xl border border-sky-200 bg-gradient-to-r from-sky-50 via-sky-50 to-indigo-50 p-5 shadow-md sm:p-6"
    >
      <div className="flex items-start gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-indigo-600 text-white shadow-md">
          <Clock className="size-5" />
        </div>
        <div className="space-y-1">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-sky-700">
            Cupo por asignar
          </p>
          <h3 className="text-lg font-black tracking-tight text-sky-900">
            Tu pago esta registrado y hay cupos disponibles
          </h3>
          <p className="max-w-xl text-sm leading-relaxed text-sky-900/80">
            Este participante todavia no tiene su cupo pagado asignado. No hace
            falta pagar de nuevo: el Comite Organizador habilita el cupo y, en
            cuanto se asigne, podra unirse a un equipo.
          </p>
        </div>
      </div>
    </div>
  );
}

function AmpliarCallout({ bloqueados }: { bloqueados: number }) {
  return (
    <div
      aria-live="polite"
      className="flex items-start gap-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
    >
      <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
        <Layers className="size-5" />
      </div>
      <div className="space-y-1">
        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
          Ampliacion de cupos
        </p>
        <h3 className="text-lg font-black tracking-tight text-slate-800">
          Amplia tus cupos para desbloquear a {bloqueados}{" "}
          {bloqueados === 1 ? "participante" : "participantes"}
        </h3>
        <p className="max-w-xl text-sm leading-relaxed text-slate-600">
          No hay cupos pagados disponibles y no hay pagos pendientes. Solicita
          una ampliacion de cupos al Comite Organizador para poder asignar a los
          participantes bloqueados.
        </p>
      </div>
    </div>
  );
}
