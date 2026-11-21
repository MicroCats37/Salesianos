import { CalendarClock, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatearHorario } from "../../utils/competencias.fecha.utils";
import type { EncuentroPublico } from "../schemas/encuentro-publico.schema";
import { etiquetaEstadoPublico } from "../utils/encuentro-publico.estados.utils";

/**
 * TarjetaEncuentroPublico — one published encounter.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * The card shows what the SERVER published and nothing else:
 *
 * - the round it belongs to;
 * - the two slots, with the name of the team and its score;
 * - the schedule, in the timezone of the edition;
 * - the WINNER, as the backend published it.
 *
 * **The winner is NEVER derived from the score.** The card prints the
 * `ganador_equipo_nombre` that travelled in the answer, and it prints the
 * score as what it is: information (`GOV-02-RB-05c`).
 *
 * The card is NOT a link: the public surface has no route per encounter, and
 * a card that looks clickable but goes nowhere is a broken promise.
 */
export interface TarjetaEncuentroPublicoProps {
  /** The encounter published by the server. */
  encuentro: EncuentroPublico;
  /** The class names of the card. */
  className?: string;
}

/** The name of a slot when the team is not decided yet. */
const EQUIPO_POR_DEFINIR = "Equipo por definir";

/**
 * The score of a slot.
 *
 * An ABSENT score is an absence, not a zero: the card prints a dash instead
 * of a number that nobody published.
 */
function puntajeDe(valor: number | null): string {
  return valor === null ? "—" : String(valor);
}

export function TarjetaEncuentroPublico({
  encuentro,
  className,
}: TarjetaEncuentroPublicoProps) {
  const horario = formatearHorario(
    encuentro.inicio_programado,
    encuentro.fin_programado,
  );
  const hayPuntaje =
    encuentro.puntaje_1 !== null || encuentro.puntaje_2 !== null;

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

          return (
            <li
              key={participante.slot}
              className="flex items-center justify-between gap-3"
            >
              <span
                className={
                  esGanador
                    ? "text-base font-black text-foreground"
                    : "text-base font-semibold text-foreground"
                }
              >
                {participante.equipo_nombre ?? EQUIPO_POR_DEFINIR}
              </span>
              <span className="font-heading text-2xl font-black tabular-nums text-foreground">
                {puntajeDe(
                  participante.slot === "PARTICIPANTE_1"
                    ? encuentro.puntaje_1
                    : encuentro.puntaje_2,
                )}
                <span className="sr-only">
                  {hayPuntaje ? " de marcador" : " sin marcador"}
                </span>
              </span>
            </li>
          );
        })}
      </ul>

      {encuentro.marcador_detalle ? (
        <p className="text-sm text-muted-foreground">
          {encuentro.marcador_detalle}
        </p>
      ) : null}

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

      {encuentro.es_bye ? (
        <p className="text-sm text-muted-foreground">Pase libre</p>
      ) : null}
    </article>
  );
}
