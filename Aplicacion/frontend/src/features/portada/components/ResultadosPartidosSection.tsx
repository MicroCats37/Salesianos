"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { useEncuentrosPublicos } from "@/features/competencias/publico/hooks/useEncuentrosPublicos";
import { useEncuentrosPublicosRealtime } from "@/features/competencias/publico/hooks/useEncuentrosPublicosRealtime";
import type { PartidoTorneo } from "@/features/competencias/publico/schemas/torneo-publico.schema";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { RUTAS } from "@/lib/routes";

/**
 * ResultadosPartidosSection — the compact summary of the matches.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * ## It is NOT the live stream
 *
 * A match in game is NOT a video: the streaming section (`LiveSection`) is
 * the transmission and this section is the STATE of the tournament. They are
 * two different facts read from two different routes, and this section never
 * claims that a video exists.
 *
 * ## It summarizes, the page shows
 *
 * The landing shows a couple of encounters of each bucket and links to the
 * dedicated page, which shows all of them. The limit is PRESENTATION: it
 * decides how many cards fit in a landing, never what exists.
 */
const MAXIMO_POR_CUBO = 2;

/** One bucket of the summary. */
interface GrupoProps {
  /** The title of the bucket. */
  titulo: string;
  /** The encounters of the bucket. */
  encuentros: PartidoTorneo[];
  /** What the bucket says when it is empty. */
  vacio: string;
}

function Grupo({ titulo, encuentros, vacio }: GrupoProps) {
  return (
    <section aria-label={titulo} className="flex flex-col gap-3">
      <h3 className="text-eyebrow-brand text-muted-foreground">{titulo}</h3>
      {encuentros.length === 0 ? (
        <p className="text-sm text-muted-foreground">{vacio}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {encuentros.map((encuentro) => (
            <li key={encuentro.id}>
              <article className="rounded-[var(--radius-lg)] border border-border bg-surface-raised p-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <strong>{encuentro.home_name}</strong>
                  <span className="font-black text-primary">
                    {encuentro.status === "scheduled"
                      ? "VS"
                      : `${encuentro.home_score ?? "—"} : ${encuentro.away_score ?? "—"}`}
                  </span>
                  <strong>{encuentro.away_name}</strong>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  {encuentro.group_id
                    ? `Grupo ${encuentro.group_id}`
                    : "Llaves finales"}
                  {encuentro.court ? ` · Cancha ${encuentro.court}` : ""}
                </p>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function ResultadosPartidosSection() {
  const partidos = useEncuentrosPublicos();
  useEncuentrosPublicosRealtime();

  const todos = partidos.data
    ? [
        ...partidos.data.groups.flatMap((grupo) => grupo.matches),
        ...partidos.data.knockout,
      ]
    : [];
  const enVivo = todos.filter((partido) =>
    ["live", "halftime", "extra", "penalties"].includes(partido.status),
  );
  const proximos = todos.filter(
    (partido) =>
      partido.status === "scheduled" && partido.home_id && partido.away_id,
  );
  const finalizados = todos.filter((partido) => partido.status === "final");
  const total = todos.length;
  const hayPartidos = total > 0;

  return (
    <PortadaSection
      id="partidos"
      eyebrow={COPY.partidos.eyebrow}
      titulo={[...COPY.partidos.titulo]}
      destacado={COPY.partidos.destacado}
      copy={COPY.partidos.copy}
      altura="auto"
    >
      <div className="mt-10 flex flex-col gap-8">
        {partidos.isPending ? (
          <p className="text-sm text-muted-foreground">
            {COPY.partidos.cargando}
          </p>
        ) : null}

        {partidos.isError ? (
          <p className="text-sm text-destructive">{COPY.partidos.error}</p>
        ) : null}

        {!partidos.isPending && !partidos.isError && !hayPartidos ? (
          <p className="text-sm text-muted-foreground">{COPY.partidos.vacio}</p>
        ) : null}

        {hayPartidos && partidos.data ? (
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <Grupo
              titulo="En vivo"
              vacio="Ahora mismo no hay ningún partido en juego."
              encuentros={enVivo.slice(0, MAXIMO_POR_CUBO)}
            />
            <Grupo
              titulo="Próximos"
              vacio="No hay partidos programados por ahora."
              encuentros={proximos.slice(0, MAXIMO_POR_CUBO)}
            />
            <Grupo
              titulo="Últimos resultados"
              vacio="Todavía no hay resultados publicados."
              encuentros={finalizados.slice(0, MAXIMO_POR_CUBO)}
            />
          </div>
        ) : null}

        <div>
          <Link
            href={RUTAS.publico.partidos}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            {COPY.partidos.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </PortadaSection>
  );
}
