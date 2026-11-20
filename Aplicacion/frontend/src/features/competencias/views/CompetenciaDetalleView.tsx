import { Swords } from "lucide-react";
import Link from "next/link";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import { ChipEstadoCompetencia } from "../components/ChipEstadoCompetencia";
import { GestionEquiposCompetencia } from "../components/GestionEquiposCompetencia";
import { ListaEncuentros } from "../components/ListaEncuentros";
import { ListaEquiposCompetencia } from "../components/ListaEquiposCompetencia";
import type {
  CompetenciaDetalle,
  EstadoVistaCompetencias,
} from "../types/competencia.types";
import { estadoCompetencia } from "../utils/competencias.estados.utils";
import { formatearDia } from "../utils/competencias.fecha.utils";

/**
 * CompetenciaDetalleView - `ADM-11`, the operational centre of a
 * competition.
 *
 * A competition is a bracket that is being built: the teams enter by hand,
 * the rounds are created by hand and an encounter may start with no
 * participants at all. An empty bracket is a LEGITIMATE state, so every block
 * has its OWN empty state with its own call to action (`RB-05` ADM-11).
 *
 * The match detail of the encounters below opens THE panel of the area, the
 * same one the agenda and the bracket use.
 */
export function CompetenciaDetalleView({
  id,
  estado = "sin-datos",
  detalle,
}: {
  /** The identifier of the competition, from the URL. */
  id: string;
  estado?: EstadoVistaCompetencias;
  detalle?: CompetenciaDetalle;
}) {
  const equipos = detalle?.equipos ?? [];
  const encuentros = (detalle?.rondas ?? []).flatMap(
    (ronda) => ronda.encuentros,
  );

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-11"
        title="Ver la ficha operativa de una competencia"
        description="Los equipos que participan, las rondas del cuadro y los encuentros programados, con su estado y su orden."
        meta={
          detalle
            ? [
                { etiqueta: "Competencia", valor: detalle.nombre },
                {
                  etiqueta: "Disciplina",
                  valor: detalle.disciplina_nombre,
                },
                { etiqueta: "Edición", valor: detalle.edicion_nombre },
              ]
            : [{ etiqueta: "Competencia", valor: id }]
        }
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

      <AdminNotice title="Una versión desactualizada no se aplica sola">
        Cada encuentro tiene su propia versión. Si otra persona lo cambió
        mientras este panel estaba abierto, el servidor rechaza el cambio y esta
        pantalla te pide que actualices y revises: nunca aplica en silencio lo
        que escribiste antes.
      </AdminNotice>

      {estado === "cargando" ? (
        <div role="status" aria-live="polite" className="flex flex-col gap-3">
          <span className="sr-only">Cargando la competencia…</span>
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : estado === "sin-permiso" ? (
        <ShellPermissionDenied title="No tienes permiso para ver esta sección" />
      ) : estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar esta competencia"
          description="El servidor no devolvió el detalle. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
          accion={{ label: "Reintentar" }}
        />
      ) : estado !== "listo" ? (
        <AdminPanel
          title="Ficha de la competencia"
          description="Los equipos, las rondas y los encuentros de la competencia."
        >
          <AdminEmptyState
            icon={Swords}
            title="Todavía no hay una ficha que mostrar"
            description="El servicio de administración de competencias todavía no está disponible en el backend. Cuando lo esté, aquí se leerán los equipos con su motivo de elegibilidad, las rondas y los encuentros programados."
          />
        </AdminPanel>
      ) : (
        <>
          <AdminPanel
            title="La competencia"
            description="Su disciplina, su día y su estado dentro del cuadro."
          >
            <div className="flex flex-wrap items-center gap-3">
              <ChipEstadoCompetencia
                estado={estadoCompetencia(detalle?.estado ?? "")}
              />
              <span className="text-sm text-muted-foreground">
                {formatearDia(detalle?.fecha) ?? "Sin día publicado"}
              </span>
            </div>
          </AdminPanel>

          <AdminPanel
            title="Equipos"
            description="Los equipos de la competencia, con su orden manual y su estado."
          >
            <GestionEquiposCompetencia
              competenciaId={id}
              equipos={equipos}
              bloqueado={(detalle?.rondas.length ?? 0) > 0}
            />
            <ListaEquiposCompetencia equipos={equipos} />
          </AdminPanel>

          <AdminPanel
            title="Encuentros"
            description="Los cruces de la competencia con su horario, su marcador y su estado."
          >
            <ListaEncuentros encuentros={encuentros} />
          </AdminPanel>
        </>
      )}
    </div>
  );
}
