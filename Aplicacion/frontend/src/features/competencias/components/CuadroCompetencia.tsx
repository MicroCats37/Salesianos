import { GitBranch } from "lucide-react";
import { AdminEmptyState } from "@/features/admin/components";
import type {
  Encuentro,
  Ronda,
  VistaPreviaAvance,
  VistaPreviaCorreccion,
} from "../types/competencia.types";
import { estadoRonda } from "../utils/competencias.estados.utils";
import { TarjetaEncuentro } from "./TarjetaEncuentro";

/**
 * CuadroCompetencia - the bracket.
 *
 * The bracket is READ HORIZONTALLY: one column per round, one card per
 * encounter, and the winner is carried to the next column. It is the one
 * memorable surface of the area, so everything around it stays quiet.
 *
 * The scroll container IS the bracket (`GOV-02-RB-05e`): a native scroll
 * region with `tabIndex={0}`, so the keyboard can reach it and the page
 * NEVER scrolls sideways. The local `scroll-area` primitive was compared and
 * rejected for this surface because it renders only a VERTICAL scrollbar and
 * the bracket needs a horizontal one with a visible focus.
 *
 * The round indicators are TEXT, never dots: a reader who does not see the
 * shape of the bracket still knows which round it is.
 */
export function CuadroCompetencia({
  rondas,
  destinosPorEncuentro,
  vistaPreviaAvancePorEncuentro,
  vistaPreviaCorreccionPorEncuentro,
}: {
  rondas: Ronda[];
  /**
   * The encounters that can receive the winner of each encounter.
   *
   * They travel as a PROP because the bracket is a presentational component:
   * it never reads the cache by itself.
   */
  destinosPorEncuentro?: Record<string, Encuentro[]>;
  vistaPreviaAvancePorEncuentro?: Record<string, VistaPreviaAvance>;
  vistaPreviaCorreccionPorEncuentro?: Record<string, VistaPreviaCorreccion>;
}) {
  if (rondas.length === 0) {
    return (
      <AdminEmptyState
        icon={GitBranch}
        title="Todavía no hay rondas en esta competencia"
        description="Un cuadro se construye con rondas y con encuentros, y ambos se crean a mano: el sistema no siembra un cuadro por su cuenta. Añade la primera ronda para empezar a montar el cruce."
      />
    );
  }

  return (
    <div
      role="region"
      aria-label="Cuadro de la competencia, desplazable en horizontal"
      tabIndex={0}
      className="overflow-x-auto rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
    >
      <div className="flex min-w-max flex-col gap-6 md:flex-row md:items-start md:gap-4">
        {rondas.map((ronda) => (
          <section
            key={ronda.id}
            aria-labelledby={`ronda-${ronda.id}`}
            className="flex w-64 shrink-0 flex-col gap-3 md:w-72"
          >
            <header className="flex items-center justify-between gap-2">
              <h3
                id={`ronda-${ronda.id}`}
                className="text-sm font-semibold text-foreground"
              >
                {ronda.etiqueta}
              </h3>
              <span className="text-caption text-muted-foreground">
                {estadoRonda(ronda.estado).estado.etiqueta}
              </span>
            </header>

            {ronda.encuentros.length > 0 ? (
              <ul className="flex flex-col gap-3">
                {ronda.encuentros.map((encuentro) => (
                  <li key={encuentro.id}>
                    <TarjetaEncuentro
                      encuentro={encuentro}
                      destinos={destinosPorEncuentro?.[encuentro.id]}
                      vistaPreviaAvance={
                        vistaPreviaAvancePorEncuentro?.[encuentro.id]
                      }
                      vistaPreviaCorreccion={
                        vistaPreviaCorreccionPorEncuentro?.[encuentro.id]
                      }
                    />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="rounded-[var(--radius-md)] border border-dashed border-border p-3 text-caption text-muted-foreground">
                Esta ronda todavía no tiene encuentros.
              </p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
