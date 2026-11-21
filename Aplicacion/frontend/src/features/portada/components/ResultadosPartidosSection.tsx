"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { TarjetaEncuentroPublico } from "@/features/competencias/publico/components/TarjetaEncuentroPublico";
import { useEncuentrosPublicos } from "@/features/competencias/publico/hooks/useEncuentrosPublicos";
import { useEncuentrosPublicosRealtime } from "@/features/competencias/publico/hooks/useEncuentrosPublicosRealtime";
import type { EncuentroPublico } from "@/features/competencias/publico/schemas/encuentro-publico.schema";
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
  encuentros: EncuentroPublico[];
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
              <TarjetaEncuentroPublico
                encuentro={encuentro}
                className="p-3 text-sm"
              />
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

  const total = partidos.data?.total ?? 0;
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
              encuentros={partidos.data.en_vivo.slice(0, MAXIMO_POR_CUBO)}
            />
            <Grupo
              titulo="Próximos"
              vacio="No hay partidos programados por ahora."
              encuentros={partidos.data.proximos.slice(0, MAXIMO_POR_CUBO)}
            />
            <Grupo
              titulo="Últimos resultados"
              vacio="Todavía no hay resultados publicados."
              encuentros={partidos.data.finalizados.slice(0, MAXIMO_POR_CUBO)}
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
