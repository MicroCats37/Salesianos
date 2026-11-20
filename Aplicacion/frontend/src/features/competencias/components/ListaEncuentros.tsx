import { CalendarClock } from "lucide-react";
import { AdminEmptyState } from "@/features/admin/components";
import { TarjetaEncuentro } from "./TarjetaEncuentro";
import { formatearInstante } from "../utils/competencias.fecha.utils";
import type {
  Encuentro,
  VistaPreviaAvance,
  VistaPreviaCorreccion,
} from "../types/competencia.types";

/**
 * ListaEncuentros - the encounters of a competition or of a day.
 *
 * The same card of the bracket opens the same panel, so the detail of an
 * encounter reads IDENTICALLY in the competition, in the agenda and in the
 * bracket (`GOV-02-RB-05a`).
 *
 * The agenda is TEMPORAL: the encounters are grouped by the day the backend
 * returned and the local time of the edition is shown next to them.
 */
export function ListaEncuentros({
  encuentros,
  vistaPreviaAvancePorEncuentro,
  vistaPreviaCorreccionPorEncuentro,
}: {
  encuentros: Encuentro[];
  vistaPreviaAvancePorEncuentro?: Record<string, VistaPreviaAvance>;
  vistaPreviaCorreccionPorEncuentro?: Record<string, VistaPreviaCorreccion>;
}) {
  if (encuentros.length === 0) {
    return (
      <AdminEmptyState
        icon={CalendarClock}
        title="No hay encuentros que mostrar"
        description="Los encuentros se crean sobre una ronda, a mano. Un cuadro parcial es legible y editable: por eso este bloque tiene su propio estado vacío."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {encuentros.map((encuentro) => {
        const inicio = formatearInstante(encuentro.inicio_programado);
        return (
          <li key={encuentro.id} className="flex flex-col gap-1">
            {inicio ? (
              <p className="text-caption text-muted-foreground">
                <time dateTime={encuentro.inicio_programado ?? undefined}>
                  {inicio}
                </time>
              </p>
            ) : null}
            <TarjetaEncuentro
              encuentro={encuentro}
              vistaPreviaAvance={
                vistaPreviaAvancePorEncuentro?.[encuentro.id]
              }
              vistaPreviaCorreccion={
                vistaPreviaCorreccionPorEncuentro?.[encuentro.id]
              }
            />
          </li>
        );
      })}
    </ul>
  );
}
