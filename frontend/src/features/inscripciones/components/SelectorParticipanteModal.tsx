"use client";

import { CheckCircle2, Lock, Search, ShieldAlert, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { ModalShell } from "@/components-app/forms/ModalShell";
import { getErrorMessage } from "@/errors";
import { cn } from "@/lib/utils";
import { useAsignarParticipanteAEquipo } from "../hooks/useAsignarParticipanteAEquipo";
import { useElegiblesEquipo } from "../hooks/useElegiblesEquipo";
import type { ElegibleOut } from "../services/elegibles.service";
import type { EquipoDetalleOut } from "../services/inscripcion.service";
import {
  type AsignacionEstado,
  asignacionEstadoDeCandidato,
} from "../utils/asignacion.estado";
import { poolGuiaSelectorVacio } from "../utils/pool.primero";
import { estadoConfig } from "./PoolParticipanteCard";

interface SelectorParticipanteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inscripcionId: string;
  /** Teams the responsable can assign to. */
  equipos: EquipoDetalleOut[];
  /** Team preselected when the modal opens. */
  equipoInicialId?: string | null;
  /**
   * Candidate preselected when the modal opens (e.g. the "Asignar" button of a
   * pool card). Ignored when the candidate is not assignable.
   */
  candidatoInicialId?: string | null;
}

/**
 * Team-scoped participant selector.
 *
 * It replaces the drag-and-drop gesture as the assignment interaction: the
 * backend owns the eligibility (`asignable`, `ya_en_disciplina`,
 * `estado_pool`) and this modal only renders it.
 *
 * One paid cup authorises the person in EVERY contracted discipline, so the
 * modal can switch the target team: a candidate that already plays in another
 * discipline is offered here, and a candidate that already plays in the
 * SELECTED discipline is shown as disabled with the R11 reason.
 *
 * The selector ONLY ASSIGNS: registering a participant happens in the pool.
 * That is why there is no "register a new participant" action here — the
 * empty state points back to the pool instead.
 */
export function SelectorParticipanteModal({
  open,
  onOpenChange,
  inscripcionId,
  equipos,
  equipoInicialId,
  candidatoInicialId,
}: SelectorParticipanteModalProps) {
  const [equipoId, setEquipoId] = useState<string | null>(
    equipoInicialId ?? equipos[0]?.id ?? null,
  );
  const [busqueda, setBusqueda] = useState("");
  const [seleccionId, setSeleccionId] = useState<string | null>(
    candidatoInicialId ?? null,
  );
  const [errorAsignacion, setErrorAsignacion] = useState<string | null>(null);

  const {
    data,
    isLoading,
    error: queryError,
  } = useElegiblesEquipo(inscripcionId, open ? equipoId : null);

  const asignar = useAsignarParticipanteAEquipo(inscripcionId);

  const equipoPorDefectoId = equipos[0]?.id ?? null;

  // Reset the transient state whenever the modal is (re)opened.
  useEffect(() => {
    if (!open) return;
    setEquipoId(equipoInicialId ?? equipoPorDefectoId);
    setBusqueda("");
    setSeleccionId(candidatoInicialId ?? null);
    setErrorAsignacion(null);
  }, [open, equipoInicialId, candidatoInicialId, equipoPorDefectoId]);

  const equipo = useMemo(
    () => equipos.find((e) => e.id === equipoId) ?? null,
    [equipos, equipoId],
  );

  const elegibles = useMemo(() => data?.elegibles ?? [], [data]);

  const filtrados = useMemo(() => {
    const term = busqueda.trim().toLowerCase();
    if (!term) return elegibles;
    return elegibles.filter((candidato) => {
      const persona = candidato.persona;
      return (
        persona.nombre.toLowerCase().includes(term) ||
        (persona.numero_documento ?? "").toLowerCase().includes(term)
      );
    });
  }, [elegibles, busqueda]);

  const seleccionado = useMemo(
    () => elegibles.find((candidato) => candidato.id === seleccionId) ?? null,
    [elegibles, seleccionId],
  );

  const puedeAsignar =
    seleccionado !== null &&
    asignacionEstadoDeCandidato(seleccionado) === "asignable";

  /** Switching the team invalidates the current selection. */
  function handleSelectTeam(nextEquipoId: string) {
    setEquipoId(nextEquipoId);
    setSeleccionId(null);
    setBusqueda("");
    setErrorAsignacion(null);
  }

  async function handlePrimary() {
    if (!seleccionado || !puedeAsignar || !equipo) return;
    setErrorAsignacion(null);
    try {
      await asignar.mutateAsync({
        inscripcionPersonaId: seleccionado.id,
        candidato: seleccionado,
        equipo,
      });
      // The mutation notifies with the backend message; the modal closes only
      // when the backend accepted the assignment.
      onOpenChange(false);
    } catch (e) {
      // The modal STAYS OPEN so the responsable can pick another candidate.
      setErrorAsignacion(getErrorMessage(e));
    }
  }

  return (
    <ModalShell
      open={open}
      onOpenChange={onOpenChange}
      title="Agregar participante al equipo"
      description="Selecciona a una persona con cupo pagado. Un solo cupo habilita a la persona en todas las disciplinas contratadas, pero nunca dos veces en la misma."
      eyebrow={equipo?.disciplina.sigla}
      icon={<Users className="size-5 text-primary" />}
      size="lg"
      primaryLabel="Asignar al equipo"
      primaryLoadingLabel="Asignando..."
      primaryLoading={asignar.isPending}
      primaryDisabled={!puedeAsignar}
      onPrimary={handlePrimary}
      secondaryLabel="Cerrar"
      bodyClassName="space-y-4 sm:w-[520px]"
    >
      {/* ── Target team ── */}
      {equipos.length > 1 && (
        <fieldset className="flex flex-wrap gap-2">
          <legend className="sr-only">Equipo destino</legend>
          {equipos.map((opcion) => {
            const activa = opcion.id === equipoId;
            return (
              <button
                key={opcion.id}
                type="button"
                onClick={() => handleSelectTeam(opcion.id)}
                aria-pressed={activa}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
                  activa
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-slate-200 bg-white text-slate-600 hover:border-primary/40 hover:text-primary",
                )}
              >
                {opcion.disciplina.sigla}
                <span className="font-normal">{opcion.nombre}</span>
              </button>
            );
          })}
        </fieldset>
      )}

      {/* ── Sticky search header ── */}
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <Input
          value={busqueda}
          onChange={(event) => setBusqueda(event.target.value)}
          placeholder="Buscar por nombre o documento"
          aria-label="Buscar participante"
          className="h-10 pl-9"
        />
      </div>

      {/* ── Error panel ── */}
      {queryError && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {queryError.message}
        </div>
      )}

      {errorAsignacion && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {errorAsignacion}
        </div>
      )}

      {/* ── Loading ── */}
      {isLoading && (
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-200 border-t-[#312e8e]" />
          Cargando participantes elegibles...
        </div>
      )}

      {/* ── Empty ── */}
      {!isLoading && !queryError && filtrados.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-sky-50 text-sky-600">
            <Users className="size-5" />
          </div>
          {elegibles.length === 0 ? (
            <>
              <p className="text-sm font-medium text-gray-700">
                {poolGuiaSelectorVacio().titulo}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {poolGuiaSelectorVacio().descripcion}
              </p>
            </>
          ) : busqueda.trim() ? (
            <>
              <p className="text-sm font-medium text-gray-700">
                Ningun participante coincide con la busqueda.
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Prueba con el nombre o el documento de la persona.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-gray-700">
                Nadie puede entrar a este equipo todavía.
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Hay {elegibles.length}{" "}
                {elegibles.length === 1 ? "persona" : "personas"} con cupo
                pagado, pero ninguna puede entrar aquí:
              </p>
              <ul className="mx-auto mt-3 max-w-sm space-y-1 text-left">
                {elegibles.map((candidato) => (
                  <li
                    key={candidato.id}
                    className="flex items-start gap-2 text-xs text-slate-600"
                  >
                    <span className="mt-1.5 size-1 shrink-0 rounded-full bg-slate-400" />
                    <span>
                      <span className="font-semibold text-slate-800">
                        {candidato.persona.nombre}
                      </span>
                      {" — "}
                      {candidato.motivo_no_asignable ??
                        candidato.motivo_bloqueo ??
                        "No puede asignarse a este equipo."}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {/* ── Candidate list ── */}
      {!isLoading && !queryError && filtrados.length > 0 && (
        <ul className="max-h-[60vh] space-y-2 sm:max-h-[420px]">
          {filtrados.map((candidato) => (
            <li key={candidato.id}>
              <CandidatoRow
                candidato={candidato}
                selected={candidato.id === seleccionId}
                onSelect={() => setSeleccionId(candidato.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </ModalShell>
  );
}

/**
 * One candidate row.
 *
 * The visual language is the one of the pool card (same chips, same borders)
 * so the responsible sees ONE system, not two.
 */
function CandidatoRow({
  candidato,
  selected,
  onSelect,
}: {
  candidato: ElegibleOut;
  selected: boolean;
  onSelect: () => void;
}) {
  const estado: AsignacionEstado = asignacionEstadoDeCandidato(candidato);
  const bloqueado = estado !== "asignable";

  const motivo = bloqueado
    ? (candidato.motivo_no_asignable ?? candidato.motivo_bloqueo)
    : null;

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={bloqueado}
      aria-pressed={selected}
      className={cn(
        "flex w-full items-start gap-3 rounded-xl border bg-white px-3 py-2.5 text-left shadow-sm transition-colors",
        bloqueado
          ? "cursor-not-allowed opacity-70"
          : "hover:border-primary/40 hover:bg-primary/5",
        selected && "border-primary ring-2 ring-primary/30",
      )}
    >
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-1.5">
          <span className="truncate font-medium text-gray-900">
            {candidato.persona.nombre}
          </span>
          {selected && (
            <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
              <CheckCircle2 className="size-3" />
              Seleccionado
            </span>
          )}
        </span>

        <span className="mt-0.5 block text-xs text-gray-500">
          {candidato.persona.numero_documento || "—"}
        </span>

        {/* Disciplines already used — one cup, several disciplines. */}
        {candidato.disciplinas_asignadas.length > 0 && (
          <span className="mt-1.5 flex flex-wrap gap-1">
            {candidato.disciplinas_asignadas.map((asignada) => (
              <span
                key={`${asignada.equipo_id}-${asignada.disciplina.id}`}
                className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700"
                title={`Ya juega en ${asignada.equipo_nombre}`}
              >
                {asignada.disciplina.sigla}
                <span className="font-normal">· {asignada.equipo_nombre}</span>
              </span>
            ))}
          </span>
        )}

        {motivo && (
          <span className="mt-1 block text-xs text-slate-500">{motivo}</span>
        )}
      </span>

      <span className="flex shrink-0 flex-col items-end gap-1">
        {estado === "ya_en_disciplina" ? (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
            <ShieldAlert className="size-3" />
            Ya en esta disciplina
          </span>
        ) : estado === "no_asignable" ? (
          // The backend blocked the candidate for a domain rule (it HAS a paid
          // cup and does not play here yet). The reason is rendered verbatim
          // below the row — the chip never guesses which rule it is.
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
            <ShieldAlert className="size-3" />
            No asignable
          </span>
        ) : estado === "sin_cupo" ? (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700">
            <Lock className="size-3" />
            {estadoConfig.bloqueado.label}
          </span>
        ) : (
          // "Asignable aquí" y NO "Listo para equipo": el pool ya usa
          // "Listo para equipo" para el hecho COMERCIAL (tiene cupo pagado).
          // Aquí la pregunta es otra: ¿puede entrar a ESTE equipo ahora?
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
            <CheckCircle2 className="size-3" />
            Asignable aquí
          </span>
        )}
      </span>
    </button>
  );
}
