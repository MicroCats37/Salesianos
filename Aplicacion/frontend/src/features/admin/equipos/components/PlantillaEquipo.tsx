import type { PlantillaEquipoOut } from "../types/equipos-admin.types";

export interface PlantillaEquipoProps {
  /** The three numbers of the roster, as the server publishes them. */
  plantilla: PlantillaEquipoOut;
  className?: string;
}

/**
 * PlantillaEquipo - the roster figures of a team.
 *
 * `GOV-02-RB-04`: the roster is shown as the THREE facts it is — how many
 * people are registered, the minimum the discipline declares and the maximum
 * it declares — and never as a derived verdict. The browser never subtracts
 * them and never decides that a team is incomplete: that is the job of the
 * `estado_operativo` of the presenter.
 *
 * The visible figure is compact and the SENTENCE is complete: a screen
 * reader reads "6 jugadores registrados; mínimo 7; máximo 10".
 */
export function PlantillaEquipo({
  plantilla,
  className,
}: PlantillaEquipoProps) {
  return (
    <span className={className}>
      <span className="tabular-nums">
        {plantilla.registrados}
        <span aria-hidden="true" className="text-foreground-muted">
          {" "}
          / {plantilla.minimo}–{plantilla.maximo}
        </span>
      </span>
      <span className="sr-only">
        {plantilla.registrados} jugadores registrados; mínimo {plantilla.minimo}
        ; máximo {plantilla.maximo}
      </span>
    </span>
  );
}
