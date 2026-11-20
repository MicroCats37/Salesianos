import Link from "next/link";
import { Button } from "@/components/ui/button";
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
 * takes `disciplina_id` and `estado` and nothing else, so no search box that
 * the service cannot honour is drawn here. The discipline filter needs the
 * catalogue of disciplines, which is another dataset: it is owed to API-05
 * with its binding.
 *
 * The select is a NATIVE control on purpose: it is the one filter widget
 * that behaves the same on a touch screen, with a keyboard and with a screen
 * reader, and it submits with the form without any state to keep in sync.
 */
export function FiltrosCompetencias({
  estado,
  accion,
}: {
  /** The state filter of the URL, if there is one. */
  estado?: string;
  /** The route the form submits to. */
  accion: string;
}) {
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

      <Button type="submit" className="min-h-11">
        Filtrar
      </Button>

      {estado ? (
        <Button variant="outline" asChild className="min-h-11">
          <Link href={accion}>Quitar el filtro</Link>
        </Button>
      ) : null}
    </form>
  );
}
