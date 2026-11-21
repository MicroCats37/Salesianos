import { ArrowLeft, CalendarClock, Trophy } from "lucide-react";
import Link from "next/link";
import { FestivalPublicPage } from "@/components/shell/FestivalPublicPage";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
} from "@/components/shell/ShellState";
import { RUTAS } from "@/lib/routes";
import { TarjetaEncuentroPublico } from "../components/TarjetaEncuentroPublico";
import type {
  EncuentroPublico,
  EncuentrosPublicos,
} from "../schemas/encuentro-publico.schema";

/**
 * EncuentrosPublicosView — the public page of the matches.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * The page shows the THREE buckets the backend publishes and NOTHING else:
 *
 * - **En vivo**: the matches that are being played right now.
 * - **Próximos**: the programme, the closest first.
 * - **Últimos resultados**: the matches with a result, the most recent first.
 *
 * It never invents a group, a table of positions, a court or a clock: the
 * backend publishes what is known and the page shows exactly that.
 *
 * The page is ANONYMOUS: a visitor without a session reads the state of the
 * published edition.
 */

/** The state of the page. */
export type EstadoVistaEncuentrosPublicos =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "error";

export interface EncuentrosPublicosViewProps {
  /** The state of the read. */
  estado?: EstadoVistaEncuentrosPublicos;
  /** The public surface published by the server. */
  encuentros?: EncuentrosPublicos;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the server
   * chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}

/** One bucket of the page. */
interface SeccionProps {
  /** The title of the bucket. */
  titulo: string;
  /** What the bucket means, in words. */
  descripcion: string;
  /** The encounters of the bucket. */
  encuentros: EncuentroPublico[];
  /** What the bucket says when it is empty. */
  vacio: string;
  /** The icon of the bucket. */
  Icono: typeof Trophy;
}

/**
 * One bucket of the public surface.
 *
 * The heading is a REAL heading (`h2`): the page is navigable with the
 * headings of its screen reader, and the state of the bucket is TEXT —never
 * colour alone.
 */
function Seccion({
  titulo,
  descripcion,
  encuentros,
  vacio,
  Icono,
}: SeccionProps) {
  return (
    <section aria-labelledby={`cubo-${titulo}`} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <span
          className="rule-gold block h-0.5 w-10 rounded-full"
          aria-hidden="true"
        />
        <h2
          id={`cubo-${titulo}`}
          className="font-heading text-2xl font-black uppercase tracking-tight text-foreground"
        >
          <Icono
            className="mr-2 inline size-5 text-primary align-middle"
            aria-hidden="true"
          />
          {titulo}
        </h2>
        <p className="max-w-measure text-lead text-muted-foreground">
          {descripcion}
        </p>
      </div>

      {encuentros.length === 0 ? (
        <p className="text-sm text-muted-foreground">{vacio}</p>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {encuentros.map((encuentro) => (
            <li key={encuentro.id}>
              <TarjetaEncuentroPublico
                encuentro={encuentro}
                className="h-full rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 shadow-[var(--elevation-sm)]"
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function EncuentrosPublicosView({
  estado = "sin-datos",
  encuentros,
  mensajeError,
  reintentar,
}: EncuentrosPublicosViewProps) {
  const total = encuentros?.total ?? 0;
  const hayPartidos = total > 0;

  return (
    <FestivalPublicPage
      eyebrow="RESULTADOS / SALESIANOS FEST"
      title={["CADA PARTIDO,", "CUENTA", "ALGO."]}
      highlighted="CUENTA."
      description="Los partidos que están en juego, los que vienen y los últimos resultados, tal como los publica el comité deportivo."
    >
      <div className="flex flex-col gap-8">
        <Link
          href={RUTAS.publico.inicio}
          className="inline-flex min-h-11 w-fit items-center gap-2 rounded-full border border-border bg-surface-raised px-4 text-sm font-semibold text-foreground transition-[transform,background-color] duration-(--motion-duration-base) hover:-translate-y-0.5 hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring active:translate-y-0"
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          Volver a la portada
        </Link>

        {estado === "cargando" ? (
          <ShellPendingState
            title="Cargando los partidos"
            description="Estamos leyendo el estado que publicó el comité deportivo."
          />
        ) : null}

        {estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar los partidos"
            description={
              mensajeError ??
              "No pudimos leer el estado de los partidos en este momento. Vuelve a intentarlo en unos segundos."
            }
            accion={
              reintentar
                ? { label: "Reintentar", onClick: reintentar }
                : undefined
            }
          />
        ) : null}

        {estado === "listo" && !hayPartidos ? (
          <RouteEmptyState
            icon={Trophy}
            title="Todavía no hay partidos publicados"
            description="El comité deportivo publica aquí los partidos del cuadro. Vuelve cuando se abra el cuadro."
          />
        ) : null}

        {estado === "listo" && hayPartidos && encuentros ? (
          <>
            <Seccion
              titulo="En vivo"
              descripcion="Los partidos que se están jugando ahora mismo."
              vacio="Ahora mismo no hay ningún partido en juego."
              encuentros={encuentros.en_vivo}
              Icono={Trophy}
            />

            <Seccion
              titulo="Próximos"
              descripcion="Los próximos partidos del cuadro, el más cercano primero."
              vacio="No hay partidos programados por ahora."
              encuentros={encuentros.proximos}
              Icono={CalendarClock}
            />

            <Seccion
              titulo="Últimos resultados"
              descripcion="Los partidos que ya tienen resultado, el más reciente primero."
              vacio="Todavía no hay resultados publicados."
              encuentros={encuentros.finalizados}
              Icono={Trophy}
            />
          </>
        ) : null}
      </div>
    </FestivalPublicPage>
  );
}
