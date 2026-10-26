"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { AdminEstadoBadge } from "@/features/admin/components";
import type { CompetenciaDetalle } from "../schemas";
import {
  estadoEquipoCompetenciaLabel,
  estadoEquipoCompetenciaTone,
  estadoRondaLabel,
  estadoRondaTone,
} from "../utils/competencias.estado.utils";
import { CompetenciaEncuentroAltaEditor } from "./editors/CompetenciaEncuentroEditor";
import {
  CompetenciaEquipoAltaEditor,
  CompetenciaEquipoEdicionEditor,
} from "./editors/CompetenciaEquipoEditor";
import {
  CompetenciaRondaAltaEditor,
  CompetenciaRondaEdicionEditor,
} from "./editors/CompetenciaRondaEditor";

export interface CompetenciasEditoresProps {
  /** The detail of the competition that owns the bracket. */
  detalle: CompetenciaDetalle;
}

/**
 * CompetenciasEditores — the administration of ONE competition.
 *
 * The panel hosts the editors of the teams (the MANUAL seed), of the rounds
 * and of the encounters. Every editor is a `GenericForm` with RHF and Zod,
 * and every mutation invalidates the reads of the module.
 *
 * The editors are shown one at a time: a bracket with twenty editors open
 * would be unreadable, and the administrator works on one decision at a
 * time.
 */
export function CompetenciasEditores({ detalle }: CompetenciasEditoresProps) {
  const [equipoEditando, setEquipoEditando] = useState<string | null>(null);
  const [rondaEditando, setRondaEditando] = useState<string | null>(null);

  return (
    <section className="card-elevated space-y-4 p-4">
      <header className="space-y-1">
        <h2 className="text-sm font-black text-slate-900">
          Administrar la competencia
        </h2>
        <p className="text-[11px] text-slate-500">
          La semilla, los byes y los horarios son decisiones manuales y
          auditadas del administrador.
        </p>
      </header>

      {/* Equipos — la semilla manual del cuadro. */}
      <div className="space-y-3">
        <h3 className="text-xs font-black uppercase tracking-wider text-slate-500">
          Equipos ({detalle.equipos.length})
        </h3>

        {detalle.equipos.length === 0 ? (
          <p className="text-xs text-slate-500">
            Todavía no hay equipos: el cuadro sigue vacío y es legible.
          </p>
        ) : (
          <ul className="divide-y divide-slate-50">
            {detalle.equipos.map((equipo) => (
              <li
                key={equipo.id}
                className="flex flex-wrap items-center justify-between gap-2 py-2"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#312e8e]/10 text-[11px] font-black text-[#312e8e]">
                    {equipo.orden}
                  </span>
                  <span className="truncate text-xs font-bold text-slate-800">
                    {equipo.equipo_nombre}
                  </span>
                  <AdminEstadoBadge
                    etiqueta={estadoEquipoCompetenciaLabel(equipo.estado)}
                    tono={estadoEquipoCompetenciaTone(equipo.estado)}
                  />
                </div>

                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  aria-expanded={equipoEditando === equipo.id}
                  onClick={() =>
                    setEquipoEditando(
                      equipoEditando === equipo.id ? null : equipo.id,
                    )
                  }
                >
                  <Pencil className="mr-1.5 h-3 w-3" aria-hidden="true" />
                  Editar
                </Button>
              </li>
            ))}
          </ul>
        )}

        {equipoEditando ? (
          <EquipoEnEdicion
            detalle={detalle}
            equipoId={equipoEditando}
            onCerrar={() => setEquipoEditando(null)}
          />
        ) : null}

        <CompetenciaEquipoAltaEditor competenciaId={detalle.id} />
      </div>

      {/* Rondas — las columnas del cuadro. */}
      <div className="space-y-3">
        <h3 className="text-xs font-black uppercase tracking-wider text-slate-500">
          Rondas ({detalle.rondas.length})
        </h3>

        {detalle.rondas.length === 0 ? (
          <p className="text-xs text-slate-500">
            Todavía no hay rondas: el cuadro todavía no tiene columnas.
          </p>
        ) : (
          <ul className="divide-y divide-slate-50">
            {detalle.rondas.map((ronda) => (
              <li
                key={ronda.id}
                className="flex flex-wrap items-center justify-between gap-2 py-2"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="truncate text-xs font-bold text-slate-800">
                    {ronda.etiqueta}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {ronda.total_encuentros} encuentros
                  </span>
                  <AdminEstadoBadge
                    etiqueta={estadoRondaLabel(ronda.estado)}
                    tono={estadoRondaTone(ronda.estado)}
                  />
                </div>

                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  aria-expanded={rondaEditando === ronda.id}
                  onClick={() =>
                    setRondaEditando(
                      rondaEditando === ronda.id ? null : ronda.id,
                    )
                  }
                >
                  <Pencil className="mr-1.5 h-3 w-3" aria-hidden="true" />
                  Editar
                </Button>
              </li>
            ))}
          </ul>
        )}

        {rondaEditando ? (
          <RondaEnEdicion
            detalle={detalle}
            rondaId={rondaEditando}
            onCerrar={() => setRondaEditando(null)}
          />
        ) : null}

        <CompetenciaRondaAltaEditor competenciaId={detalle.id} />
      </div>

      {/* Encuentros — los cruces del cuadro. */}
      <div className="space-y-3">
        <h3 className="text-xs font-black uppercase tracking-wider text-slate-500">
          Encuentros
        </h3>
        <CompetenciaEncuentroAltaEditor competenciaId={detalle.id} />
      </div>
    </section>
  );
}

/** The editor of ONE participation. */
function EquipoEnEdicion({
  detalle,
  equipoId,
  onCerrar,
}: {
  detalle: CompetenciaDetalle;
  equipoId: string;
  onCerrar: () => void;
}) {
  const equipo = detalle.equipos.find((item) => item.id === equipoId);

  if (!equipo) return null;

  return (
    <CompetenciaEquipoEdicionEditor
      competenciaId={detalle.id}
      equipo={equipo}
      onCancel={onCerrar}
    />
  );
}

/** The editor of ONE round. */
function RondaEnEdicion({
  detalle,
  rondaId,
  onCerrar,
}: {
  detalle: CompetenciaDetalle;
  rondaId: string;
  onCerrar: () => void;
}) {
  const ronda = detalle.rondas.find((item) => item.id === rondaId);

  if (!ronda) return null;

  return (
    <CompetenciaRondaEdicionEditor
      competenciaId={detalle.id}
      ronda={ronda}
      onCancel={onCerrar}
    />
  );
}
