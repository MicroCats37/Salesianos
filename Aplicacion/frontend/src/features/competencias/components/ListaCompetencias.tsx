import Link from "next/link";
import { CalendarClock, GitBranch, Swords } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import { ChipEstadoCompetencia } from "./ChipEstadoCompetencia";
import { estadoCompetencia } from "../utils/competencias.estados.utils";
import { formatearDia } from "../utils/competencias.fecha.utils";
import type { CompetenciaListado } from "../types/competencia.types";

/**
 * ListaCompetencias - the competitions of the edition (`ADM-10`).
 *
 * ONE content, TWO readings: below 768 the row becomes a card with the
 * discipline, the day and the three entry points; from 768 the same data is
 * a table with an action column. Only one of them is in the accessibility
 * tree at a time, so nothing is read twice.
 *
 * The three entry points are three DIFFERENT LINKS with their own name — a
 * detail, a bracket and an agenda — never an icon menu without an
 * accessible name (`RB-05` ADM-10).
 */
export function ListaCompetencias({
  competencias,
}: {
  competencias: CompetenciaListado[];
}) {
  if (competencias.length === 0) {
    return (
      <AdminEmptyState
        icon={Swords}
        title="Todavía no hay competencias en esta edición"
        description="Las competencias se crean a mano, con su disciplina, su nombre y su día. Cuando la integración esté disponible, aquí se listarán con sus contadores de equipos y de encuentros."
      />
    );
  }

  return (
    <>
      <ul className="flex flex-col gap-3 md:hidden">
        {competencias.map((competencia) => (
          <li
            key={competencia.id}
            className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3"
          >
            <div className="flex flex-col gap-1">
              <p className="text-sm font-semibold text-foreground">
                {competencia.nombre}
              </p>
              <p className="text-caption text-muted-foreground">
                {competencia.disciplina_nombre}
                {formatearDia(competencia.fecha)
                  ? ` · ${formatearDia(competencia.fecha)}`
                  : ""}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <ChipEstadoCompetencia
                estado={estadoCompetencia(competencia.estado)}
              />
              <span className="text-caption text-muted-foreground tabular-nums">
                {competencia.total_equipos} equipos ·{" "}
                {competencia.total_encuentros} encuentros
              </span>
            </div>

            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                asChild
                className="min-h-11 w-full justify-start"
              >
                <Link href={RUTAS.administracion.competenciaDetalle(competencia.id)}>
                  <Swords className="size-4" aria-hidden="true" />
                  Ver el detalle
                </Link>
              </Button>
              <Button
                variant="outline"
                asChild
                className="min-h-11 w-full justify-start"
              >
                <Link
                  href={RUTAS.administracion.competenciaCuadro(competencia.id)}
                >
                  <GitBranch className="size-4" aria-hidden="true" />
                  Operar el cuadro
                </Link>
              </Button>
              <Button
                variant="outline"
                asChild
                className="min-h-11 w-full justify-start"
              >
                <Link href={RUTAS.administracion.competenciaAgenda}>
                  <CalendarClock className="size-4" aria-hidden="true" />
                  Ver la agenda
                </Link>
              </Button>
            </div>
          </li>
        ))}
      </ul>

      <div className="hidden md:block">
        <AdminDataTable
          caption="Competencias de la edición"
          columns={[
            { key: "competencia", label: "Competencia" },
            { key: "disciplina", label: "Disciplina" },
            { key: "fecha", label: "Fecha" },
            { key: "estado", label: "Estado" },
            { key: "equipos", label: "Equipos", numerico: true },
            { key: "encuentros", label: "Encuentros", numerico: true },
            { key: "finalizados", label: "Finalizados", numerico: true },
            { key: "acciones", label: "Acciones" },
          ]}
          filas={competencias.map((competencia) => ({
            cells: {
              competencia: (
                <span className="font-medium text-foreground">
                  {competencia.nombre}
                </span>
              ),
              disciplina: (
                <span className="text-muted-foreground">
                  {competencia.disciplina_nombre}
                </span>
              ),
              fecha: (
                <span className="text-muted-foreground">
                  {formatearDia(competencia.fecha) ?? "—"}
                </span>
              ),
              estado: (
                <ChipEstadoCompetencia
                  estado={estadoCompetencia(competencia.estado)}
                />
              ),
              equipos: String(competencia.total_equipos),
              encuentros: String(competencia.total_encuentros),
              finalizados: String(competencia.total_encuentros_finalizados),
              acciones: (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="min-h-11"
                  >
                    <Link
                      href={RUTAS.administracion.competenciaDetalle(
                        competencia.id,
                      )}
                    >
                      Ver el detalle
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="min-h-11"
                  >
                    <Link
                      href={RUTAS.administracion.competenciaCuadro(
                        competencia.id,
                      )}
                    >
                      Operar el cuadro
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="min-h-11"
                  >
                    <Link href={RUTAS.administracion.competenciaAgenda}>
                      Ver la agenda
                    </Link>
                  </Button>
                </div>
              ),
            },
          }))}
        />
      </div>
    </>
  );
}
