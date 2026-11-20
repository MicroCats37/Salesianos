import { Swords } from "lucide-react";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import { RUTAS } from "@/lib/routes";
import { FiltrosCompetencias } from "../components/FiltrosCompetencias";
import { ListaCompetencias } from "../components/ListaCompetencias";
import type {
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
 * The default state is `sin-datos`: the module `competencias` is not
 * registered in the backend, so this view does not draw a list that does not
 * exist (`A0-RTV-01`).
 */
export function CompetenciasListaView({
  estado = "sin-datos",
  competencias = [],
  filtroEstado,
}: {
  estado?: EstadoVistaCompetencias;
  competencias?: CompetenciaListado[];
  /** The state filter of the URL. */
  filtroEstado?: string;
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
        Programar un encuentro, configurar un pase libre, registrar un
        resultado o confirmar un avance son acciones con motivo auditado y
        bloqueo optimista: si otra persona cambió la misma versión, el
        servidor rechaza el cambio y nada se escribe.
      </AdminNotice>

      <AdminPanel
        title="Competencias"
        description="Las competencias publicadas, con sus equipos y sus encuentros."
        actions={<FiltrosCompetencias estado={filtroEstado} accion={RUTAS.administracion.competencias} />}
      >
        {estado === "listo" ? (
          <ListaCompetencias competencias={competencias} />
        ) : estado === "cargando" ? (
          <div
            role="status"
            aria-live="polite"
            className="flex flex-col gap-3"
          >
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
            description="El servidor no devolvió el listado. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            accion={{ label: "Reintentar" }}
          />
        ) : (
          <AdminEmptyState
            icon={Swords}
            title="Todavía no hay competencias que mostrar"
            description="El servicio de administración de competencias todavía no está disponible en el backend, así que aquí no se dibuja ninguna lista: no hay datos de los que hablar y no se inventan. Cuando el servicio esté conectado, esta pantalla listará cada competencia con sus contadores y con sus tres entradas."
          />
        )}
      </AdminPanel>
    </div>
  );
}
