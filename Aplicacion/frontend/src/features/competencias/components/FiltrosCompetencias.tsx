import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { CategoriaDeEdicion } from "../types/competencia.types";
import { ESTADOS_COMPETENCIA } from "../utils/competencias.estados.utils";

/**
 * FiltrosCompetencias - the filters of the list of competitions.
 *
 * The bar is a NATIVE GET form: the filters live in the URL, they survive a
 * reload, they can be shared and they work without JavaScript. The list and
 * the bracket read the same filters, so the two surfaces stay coherent
 * (`RB-05` ADM-10).
 *
 * The bar offers the filters the backend ACCEPTS: `listar_competencias`
 * takes `disciplina_id`, `categoria_id` and `estado` and nothing else, so no
 * search box that the service cannot honour is drawn here. The discipline
 * filter needs the catalogue of disciplines, which is another dataset: it is
 * owed to API-05 with its binding.
 *
 * ## The filter of the band
 *
 * The competitive band is part of the IDENTITY of a competition, so the
 * operator filters by it the same way it filters by the state. The OPTIONS
 * are the bands that the catalogue of the edition publishes; the filter
 * NEVER derives which band a team belongs to.
 *
 * The select is a NATIVE control on purpose: it is the one filter widget
 * that behaves the same on a touch screen, with a keyboard and with a screen
 * reader, and it submits with the form without any state to keep in sync.
 */
export function FiltrosCompetencias({
  estado,
  categoria,
  categorias,
  accion,
}: {
  /** The state filter of the URL, if there is one. */
  estado?: string;
  /** The band filter of the URL, if there is one. */
  categoria?: string;
  /** The bands of the edition, as the catalogue publishes them. */
  categorias?: readonly CategoriaDeEdicion[];
  /** The route the form submits to. */
  accion: string;
}) {
  const hayFiltroCategoria = Boolean(categoria);
  const hayFiltroEstado = Boolean(estado);

  return (
    <form
      method="get"
      action={accion}
      className="flex flex-wrap items-end gap-3"
      aria-label="Filtros de las competencias"
    >
      <div className="flex min-w-48 flex-col gap-1">
        <label
          htmlFor="filtro-estado-competencia"
          className="text-caption text-muted-foreground"
        >
          Estado de la competencia
        </label>
        <select
          id="filtro-estado-competencia"
          name="estado"
          defaultValue={estado ?? ""}
          className="min-h-11 rounded-[var(--radius-md)] border border-border bg-surface-raised px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
        >
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS_COMPETENCIA).map(([codigo, etiqueta]) => (
            <option key={codigo} value={codigo}>
              {etiqueta}
            </option>
          ))}
        </select>
      </div>

      {categorias && categorias.length > 0 ? (
        <div className="flex min-w-48 flex-col gap-1">
          <label
            htmlFor="filtro-categoria-competencia"
            className="text-caption text-muted-foreground"
          >
            Categoría
          </label>
          <select
            id="filtro-categoria-competencia"
            name="categoria_id"
            defaultValue={categoria ?? ""}
            className="min-h-11 rounded-[var(--radius-md)] border border-border bg-surface-raised px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          >
            <option value="">Todas las categorías</option>
            {categorias.map((categoria) => (
              <option key={categoria.id} value={categoria.id}>
                {categoria.nombre}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      <Button type="submit" className="min-h-11">
        Filtrar
      </Button>

      {hayFiltroEstado || hayFiltroCategoria ? (
        <Button variant="outline" asChild className="min-h-11">
          <Link href={accion}>Quitar el filtro</Link>
        </Button>
      ) : null}
    </form>
  );
}
