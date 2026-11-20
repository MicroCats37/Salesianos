import { Swords } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-11 - the detail of a competition.
 *
 * A competition is a bracket that is being built: the teams enter by hand,
 * the rounds are created by hand, and the encounters may start with no
 * participants at all. An empty bracket is a legitimate state, not a broken
 * one.
 */
export function AdminCompetenciaDetalleView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-11"
        title="Ver la ficha operativa de una competencia"
        description="Los equipos que participan, las rondas del cuadro y los encuentros programados, con su estado y su orden."
        meta={[{ etiqueta: "Competencia", valor: id }]}
        actions={
          <>
            <Button variant="outline" asChild className="min-h-11">
              <Link href={RUTAS.administracion.competenciaCuadro(id)}>
                Operar el cuadro
              </Link>
            </Button>
            <Button asChild className="min-h-11">
              <Link href={RUTAS.administracion.competencias}>
                Volver a las competencias
              </Link>
            </Button>
          </>
        }
      />

      <AdminPanel
        title="Equipos"
        description="Los equipos de la competencia, con su orden manual y su estado."
      >
        <AdminDataTable
          caption="Equipos de la competencia"
          columns={[
            { key: "equipo", label: "Equipo" },
            { key: "disciplina", label: "Disciplina" },
            { key: "categoria", label: "Categoría" },
            { key: "orden", label: "Orden" },
            { key: "estado", label: "Estado" },
          ]}
          vacio={
            <AdminEmptyState
              icon={Swords}
              title="Todavía no hay equipos en esta competencia"
              description="El alta de equipos es manual: nunca se siembran solos. Cuando la integración esté disponible, se podrán añadir aquí los equipos activos de la misma disciplina y categoría."
            />
          }
        />
      </AdminPanel>

      <AdminPanel
        title="Rondas"
        description="Las rondas del cuadro, con su etiqueta, su orden y su número de encuentros."
      >
        <AdminDataTable
          caption="Rondas del cuadro de la competencia"
          columns={[
            { key: "ronda", label: "Ronda" },
            { key: "encuentros", label: "Encuentros" },
            { key: "estado", label: "Estado" },
          ]}
          vacio={
            <AdminEmptyState
              icon={Swords}
              title="Todavía no hay rondas"
              description="La etiqueta y el orden de una ronda son únicos dentro del cuadro. Un cuadro vacío o parcial es legible y editable: por eso cada bloque tiene su propio estado vacío."
            />
          }
        />
      </AdminPanel>

      <AdminPanel
        title="Encuentros"
        description="Los cruces de la competencia con su horario, su marcador y su estado."
      >
        <AdminEmptyState
          icon={Swords}
          title="Los encuentros se crean sobre las rondas"
          description="Los dos participantes de un encuentro son opcionales a propósito: un cuadro parcial debe poder leerse y editarse sin inventar participantes."
        />
      </AdminPanel>
    </div>
  );
}
