import { CalendarClock, Trophy } from "lucide-react";
import type { EncuentroPublico } from "@/features/competencias/publico/schemas/encuentro-publico.schema";
import { etiquetaEstadoPublico } from "@/features/competencias/publico/utils/encuentro-publico.estados.utils";
import { formatearInstante } from "@/features/competencias/utils/competencias.fecha.utils";
import { cn } from "@/lib/utils";

export interface TarjetaPartidoCuentaProps {
  /** The encounter published by the server. */
  encuentro: EncuentroPublico;
  className?: string;
}

/** The name of a slot when the team is not decided yet. */
const EQUIPO_POR_DEFINIR = "Equipo por definir";

/**
 * TarjetaPartidoCuenta - one match of the account.
 *
 * It shows what the server published: the round, the two teams with their
 * score, the schedule and the EXPLICIT winner.
 *
 * **The winner is NEVER derived from the score**: the card prints the
 * `ganador_equipo_nombre` that travelled in the answer, and the score is
 * shown as what it is: information.
 */
export function TarjetaPartidoCuenta({
  encuentro,
  className,
}: TarjetaPartidoCuentaProps) {
  const horario = formatearInstante(encuentro.inicio_programado);

  return (
    <article
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 shadow-[var(--elevation-sm)]",
        className,
      )}
    >
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <p className="text-eyebrow-brand text-muted-foreground">
          {encuentro.ronda_etiqueta}
        </p>
        <p className="text-xs font-black uppercase tracking-[0.15em] text-primary">
          {etiquetaEstadoPublico(encuentro.estado_publico)}
        </p>
      </header>

      <ul className="flex flex-col gap-2">
        {encuentro.participantes.map((participante) => {
          const esGanador =
            participante.equipo_id !== null &&
            participante.equipo_id === encuentro.ganador_equipo_id;
          const puntaje =
            participante.slot === "PARTICIPANTE_1"
              ? encuentro.puntaje_1
              : encuentro.puntaje_2;

          return (
            <li
              key={participante.slot}
              className="flex items-center justify-between gap-3"
            >
              <span
                className={cn(
                  "text-base text-foreground",
                  esGanador ? "font-black" : "font-semibold",
                )}
              >
                {participante.equipo_nombre ?? EQUIPO_POR_DEFINIR}
              </span>
              <span className="font-heading text-2xl font-black tabular-nums text-foreground">
                {puntaje === null ? "—" : puntaje}
              </span>
            </li>
          );
        })}
      </ul>

      {encuentro.ganador_equipo_nombre ? (
        <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Trophy className="size-4 text-primary" aria-hidden="true" />
          Ganó {encuentro.ganador_equipo_nombre}
        </p>
      ) : null}

      {horario ? (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <CalendarClock className="size-4" aria-hidden="true" />
          <time dateTime={encuentro.inicio_programado ?? undefined}>
            {horario}
          </time>
        </p>
      ) : null}
    </article>
  );
}
