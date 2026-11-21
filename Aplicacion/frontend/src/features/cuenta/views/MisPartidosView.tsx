import { CalendarClock, Trophy } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
} from "@/components/shell/ShellState";
import { TarjetaPartidoCuenta } from "../components/TarjetaPartidoCuenta";
import type { CuentaPartidos } from "../schemas/cuenta-partidos.schema";

/**
 * ACCOUNT-04 - "MIS PARTIDOS".
 *
 * The page shows the matches of the ACCOUNT in the three buckets the server
 * publishes: the ones in game, the ones that come and the ones that already
 * finished.
 *
 * It NEVER invents a group, a table of positions, a court or a clock: the
 * state of a match is what the committee published.
 */
export interface MisPartidosViewProps {
  /** The state of the read. */
  estado?: "sin-datos" | "cargando" | "listo" | "error";
  /** The matches of the account, when the read succeeded. */
  partidos?: CuentaPartidos;
  /** The message of the server when the read failed. */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}

/** One bucket of the page. */
function Cubo({
  titulo,
  descripcion,
  encuentros,
  vacio,
  Icono,
}: {
  titulo: string;
  descripcion: string;
  encuentros: CuentaPartidos["en_vivo"];
  vacio: string;
  Icono: typeof Trophy;
}) {
  return (
    <section
      aria-labelledby={`cuenta-cubo-${titulo}`}
      className="flex flex-col gap-4"
    >
      <div className="flex flex-col gap-1">
        <h2
          id={`cuenta-cubo-${titulo}`}
          className="font-heading text-xl font-black uppercase tracking-tight text-foreground"
        >
          <Icono
            className="mr-2 inline size-5 text-primary align-middle"
            aria-hidden="true"
          />
          {titulo}
        </h2>
        <p className="max-w-measure text-caption text-muted-foreground">
          {descripcion}
        </p>
      </div>

      {encuentros.length === 0 ? (
        <p className="text-sm text-muted-foreground">{vacio}</p>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {encuentros.map((encuentro) => (
            <li key={encuentro.id}>
              <TarjetaPartidoCuenta encuentro={encuentro} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function MisPartidosView({
  estado = "sin-datos",
  partidos,
  mensajeError,
  reintentar,
}: MisPartidosViewProps) {
  const hayPartidos = estado === "listo" && (partidos?.total ?? 0) > 0;

  return (
    <div className="flex flex-col gap-8 pb-10">
      <header className="flex flex-col gap-2">
        <p className="text-eyebrow-brand text-primary">Salesianos FEST 2026</p>
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Mis partidos
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Los partidos de tus equipos: los que están en juego, los que vienen y
          los últimos resultados.
        </p>
      </header>

      {estado === "cargando" ? (
        <ShellPendingState
          title="Cargando tus partidos"
          description="Estamos leyendo el estado que publicó el comité deportivo."
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar tus partidos"
          description={
            mensajeError ??
            "No pudimos leer el estado de tus partidos en este momento. Vuelve a intentarlo en unos segundos."
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
          title="Todavía no tienes partidos publicados"
          description="En cuanto el comité publique el cuadro, aquí verás los partidos de tus equipos."
        />
      ) : null}

      {estado === "listo" && partidos && partidos.equipos.length > 0 ? (
        <section
          aria-labelledby="cuenta-equipos"
          className="flex flex-col gap-2"
        >
          <h2
            id="cuenta-equipos"
            className="font-heading text-xl font-black uppercase tracking-tight text-foreground"
          >
            <Trophy
              className="mr-2 inline size-5 text-primary align-middle"
              aria-hidden="true"
            />
            Tus equipos
          </h2>
          <ul className="flex flex-wrap gap-2">
            {partidos.equipos.map((equipo) => (
              <li
                key={equipo.id}
                className="rounded-full border border-border bg-surface-raised px-3 py-1 text-sm text-foreground"
              >
                {equipo.equipo_nombre}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {hayPartidos && partidos ? (
        <>
          <Cubo
            titulo="En vivo"
            descripcion="Los partidos que se están jugando ahora mismo."
            vacio="Ahora mismo no hay ningún partido en juego."
            encuentros={partidos.en_vivo}
            Icono={Trophy}
          />
          <Cubo
            titulo="Próximos"
            descripcion="Los próximos partidos de tus equipos, el más cercano primero."
            vacio="No hay partidos programados por ahora."
            encuentros={partidos.proximos}
            Icono={CalendarClock}
          />
          <Cubo
            titulo="Últimos resultados"
            descripcion="Los partidos que ya tienen resultado, el más reciente primero."
            vacio="Todavía no hay resultados publicados."
            encuentros={partidos.finalizados}
            Icono={Trophy}
          />
        </>
      ) : null}
    </div>
  );
}
