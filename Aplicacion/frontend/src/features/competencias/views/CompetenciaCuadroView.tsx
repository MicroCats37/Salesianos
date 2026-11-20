import { GitBranch } from "lucide-react";
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
import { CuadroCompetencia } from "../components/CuadroCompetencia";
import { GestionEquiposCompetencia } from "../components/GestionEquiposCompetencia";
import type {
  CompetenciaEquipo,
  EstadoVistaCompetencias,
  Ronda,
  VistaPreviaAvance,
  VistaPreviaCorreccion,
} from "../types/competencia.types";

/**
 * CompetenciaCuadroView - `ADM-12`, the bracket of a competition.
 *
 * The bracket is the ONE place where the progression is visible: a column
 * per round, a card per encounter and the winner carried to the next column.
 *
 * The advance and the correction are TWO steps and TWO actions: the preview
 * says what would happen and it NEVER writes; the confirm is what writes
 * (`GOV-02-RB-05b`, `QA-K04`).
 */
export function CompetenciaCuadroView({
  id,
  estado = "sin-datos",
  rondas = [],
  equipos = [],
  generarCuadro,
  generando = false,
  vistaPreviaAvancePorEncuentro,
  vistaPreviaCorreccionPorEncuentro,
}: {
  /** The identifier of the competition, from the URL. */
  id: string;
  estado?: EstadoVistaCompetencias;
  rondas?: Ronda[];
  equipos?: CompetenciaEquipo[];
  generarCuadro?: () => Promise<unknown>;
  generando?: boolean;
  vistaPreviaAvancePorEncuentro?: Record<string, VistaPreviaAvance>;
  vistaPreviaCorreccionPorEncuentro?: Record<string, VistaPreviaCorreccion>;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-12"
        title="Operar el cuadro de encuentros"
        description="El cuadro de la competencia: una columna por ronda, una celda por encuentro, con el ganador que avanza a la siguiente."
        meta={[{ etiqueta: "Competencia", valor: id }]}
        actions={
          <>
            {rondas.length === 0 && generarCuadro ? (
              <Button
                type="button"
                className="min-h-11"
                disabled={generando}
                onClick={() => void generarCuadro()}
              >
                {generando ? "Generando cuadro..." : "Generar cuadro"}
              </Button>
            ) : null}
            <Button variant="outline" asChild className="min-h-11">
              <Link href={RUTAS.administracion.competencias}>
                Volver a las competencias
              </Link>
            </Button>
          </>
        }
      />

      <AdminNotice title="El servidor manda en el cuadro">
        Programar un encuentro, configurar un pase libre, enlazar, registrar un
        resultado o confirmar un avance son acciones con motivo auditado y
        bloqueo optimista: si otra persona cambió la misma versión, el servidor
        rechaza el cambio y nada se escribe.
      </AdminNotice>

      <AdminPanel
        title="Cuadro"
        description="Las rondas del cuadro y los encuentros de cada una."
      >
        {estado === "listo" && rondas.length === 0 ? (
          <GestionEquiposCompetencia competenciaId={id} equipos={equipos} />
        ) : null}
        {estado === "listo" ? (
          <CuadroCompetencia
            rondas={rondas}
            vistaPreviaAvancePorEncuentro={vistaPreviaAvancePorEncuentro}
            vistaPreviaCorreccionPorEncuentro={
              vistaPreviaCorreccionPorEncuentro
            }
          />
        ) : estado === "cargando" ? (
          <div role="status" aria-live="polite" className="flex flex-col gap-3">
            <span className="sr-only">Cargando el cuadro…</span>
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : estado === "sin-permiso" ? (
          <ShellPermissionDenied title="No tienes permiso para ver esta sección" />
        ) : estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar el cuadro"
            description="El servidor no devolvió las rondas ni los encuentros. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            accion={{ label: "Reintentar" }}
          />
        ) : (
          <AdminEmptyState
            icon={GitBranch}
            title="Todavía no hay un cuadro que mostrar"
            description="El servicio de administración de competencias todavía no está disponible en el backend, así que aquí no se dibuja ninguna columna de rondas. Cuando lo esté, el cuadro se pintará con una columna por ronda y una tarjeta por encuentro, con su marcador y con las acciones que el servidor admita."
          />
        )}
      </AdminPanel>
    </div>
  );
}
