"use client";

import { Users } from "lucide-react";

interface AsignacionHintProps {
  equiposCount: number;
  participantesTotal: number;
  /** Distinct people already placed (roster rows may be more). */
  personasDistintas: number;
  /** Pre-registered people waiting in the pool. */
  poolCount: number;
}

/**
 * Contextual hint about how the assignment works.
 *
 * It replaces the old drag-and-drop banner: the assignment gesture is the
 * participant selector, and one cup authorises several disciplines.
 */
export function AsignacionHint({
  equiposCount,
  participantesTotal,
  personasDistintas,
  poolCount,
}: AsignacionHintProps) {
  const hayEquipos = equiposCount > 0;
  const hayPersonas = participantesTotal > 0;
  if (!hayEquipos && poolCount === 0) {
    return null;
  }
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-violet-200/70 bg-gradient-to-r from-violet-50/80 via-sky-50/70 to-amber-50/70 p-4 shadow-sm">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-400 to-sky-500 text-white shadow-sm">
        <Users className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-x-2 text-xs font-bold uppercase tracking-wider text-violet-900">
          <span>Tip</span>
          <span className="text-[11px] font-medium normal-case tracking-normal text-violet-700">
            — registrar y asignar participantes
          </span>
        </p>
        <p className="mt-0.5 text-xs leading-snug text-slate-700 sm:text-sm">
          Registra a cada persona con{" "}
          <span className="font-semibold text-violet-900">
            Agregar participante
          </span>{" "}
          en el pool y luego toca{" "}
          <span className="font-semibold text-violet-900">Agregar jugador</span>{" "}
          en un equipo para asignarla desde el selector.
        </p>
        {hayPersonas && (
          <p className="mt-1 text-xs leading-snug text-slate-600">
            Un solo cupo pagado habilita a la misma persona en todas las
            disciplinas contratadas, pero nunca dos veces en la misma
            disciplina. Hoy hay{" "}
            <span className="font-semibold text-violet-900">
              {participantesTotal} participaciones
            </span>{" "}
            de{" "}
            <span className="font-semibold text-violet-900">
              {personasDistintas} personas
            </span>
            .
          </p>
        )}
        {poolCount > 0 && (
          <p className="mt-1 text-xs leading-snug text-slate-600">
            Las personas que esperan en el pool (
            <span className="font-semibold text-violet-900">{poolCount}</span>)
            todavia no tienen equipo.
          </p>
        )}
      </div>
    </div>
  );
}
