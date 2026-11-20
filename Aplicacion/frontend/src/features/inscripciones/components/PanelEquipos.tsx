"use client";

import { Users } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import type { EquipoInscripcion } from "../types/inscripcion.types";

export interface PanelEquiposProps {
  /** The teams declared in the registration, as the server publishes them. */
  equipos: readonly EquipoInscripcion[];
}

/**
 * PanelEquipos - the teams of a registration.
 *
 * A team is a name, the discipline it competes in, the competitive band that
 * the server derived and the state the server gave it. The minimum and the
 * maximum of the roster are NOT computed here: the discipline publishes them
 * and the state of the team is the verdict of the server.
 *
 * The band is printed as it arrives: it was derived by the server from the
 * cohort of the registration (`RN-C02`, `QA-K01`), and the browser never
 * derives it nor guesses it.
 */
export function PanelEquipos(props: PanelEquiposProps) {
  const equipos = props.equipos;

  if (equipos.length === 0) {
    return (
      <RouteEmptyState
        icon={Users}
        title="Todavía no hay equipos en esta inscripción"
        description="Los equipos se declaran al crear la inscripción. Cuando el comité valide la nómina, aquí aparecerá cada equipo con su disciplina."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {equipos.map((equipo) => (
        <li
          key={equipo.id}
          className="flex flex-col gap-1 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
        >
          <span className="text-sm font-semibold text-foreground">
            {equipo.nombre}
          </span>
          <span className="text-caption text-muted-foreground">
            {equipo.disciplina_nombre}
          </span>
          <span className="text-caption text-muted-foreground">
            Categoría: {equipo.categoria.nombre}
          </span>
          <span className="text-caption text-muted-foreground">
            Estado: {equipo.estado}
          </span>
        </li>
      ))}
    </ul>
  );
}
