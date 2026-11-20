import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import { FiltrosCompetencias } from "../components/FiltrosCompetencias";
import { ListaCompetencias } from "../components/ListaCompetencias";
import type {
  CategoriaDeEdicion,
  CompetenciaListado,
  EstadoVistaCompetencias,
} from "../types/competencia.types";

/**
 * CompetenciasListaView - `ADM-10`, the competitions of the edition.
 *
 * The route is the place where the operator CHOOSES a competition to
 * administer, so it answers three questions: which competitions exist, in
 * what state, and where do I open each one.
 *
 * ## The band of the competition
 *
 * A competition belongs to ONE competitive band, so the bar can filter by it
 * and every row names it. The OPTIONS of the filter are the bands that the
 * catalogue of the edition publishes: the view does not invent them.
 *
 * ## The states are HONEST
 *
 * The route IS registered, so there is no `sin-datos` state here: the four
 * states of a read are `cargando`, `listo`, `sin-permiso` and `error`, and
 * the error offers the action that resolves it (a retry that reads again).
 * The empty state says that the server did not return any competition: it
 * does not blame a service that IS connected.
 */
export function CompetenciasListaView({
  estado = "cargando",
  competencias = [],
  categorias = [],
  filtroEstado,
  filtroCategoria,
  reintentar,
  mensajeError,
  avisoCatalogos,
}: {
  estado?: EstadoVistaCompetencias;
  competencias?: CompetenciaListado[];
  /** The bands of the edition, as the catalogue publishes them. */
  categorias?: readonly CategoriaDeEdicion[];
  /** The state filter of the URL. */
  filtroEstado?: string;
  /** The band filter of the URL. */
  filtroCategoria?: string;
  /** The action that reads the list again. */
  reintentar?: () => void;
  /** The public prose of the failure, printed verbatim. */
  mensajeError?: string;
  /** The notice that the options of the band filter are not available. */
  avisoCatalogos?: string;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-10"
        title="Seleccionar y administrar competencias"
        description="Las competencias de la edición con sus contadores de equipos y encuentros, y el acceso a su cuadro y a su agenda."
      />

      <AdminSubnav
        ariaLabel="Secciones de competencias"
        items={[
          {
            href: RUTAS.administracion.competencias,
            label: "Lista",
            description: "Todas las competencias",
          },
          {
            href: RUTAS.administracion.competenciaAgenda,
            label: "Agenda",
            description: "Encuentros de un día",
          },
        ]}
      />

      <AdminNotice title="El servidor manda en el cuadro">
        Programar un encuentro, configurar un pase libre, registrar un resultado
        o confirmar un avance son acciones con motivo auditado y bloqueo
        optimista: si otra persona cambió la misma versión, el servidor rechaza
        el cambio y nada se escribe.
      </AdminNotice>

      <AdminPanel
        title="Competencias"
        description="Las competencias publicadas, con sus equipos y sus encuentros."
        actions={
          <div className="flex flex-col gap-2">
            <FiltrosCompetencias
              estado={filtroEstado}
              categoria={filtroCategoria}
              categorias={categorias}
              accion={RUTAS.administracion.competencias}
            />
            {avisoCatalogos ? (
              <p className="text-caption text-muted-foreground">
                {avisoCatalogos}
              </p>
            ) : null}
          </div>
        }
      >
        {estado === "cargando" ? (
          <div role="status" aria-live="polite" className="flex flex-col gap-3">
            <span className="sr-only">Cargando las competencias…</span>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : estado === "sin-permiso" ? (
          <ShellPermissionDenied title="No tienes permiso para ver esta sección" />
        ) : estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar las competencias"
            description={
              mensajeError ??
              "El servidor no devolvió el listado. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            }
            accion={{ label: "Reintentar", onClick: reintentar }}
          />
        ) : (
          <ListaCompetencias competencias={competencias} />
        )}
      </AdminPanel>
    </div>
  );
}
