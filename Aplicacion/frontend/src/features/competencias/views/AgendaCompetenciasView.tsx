import { CalendarClock } from "lucide-react";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import { ListaEncuentros } from "../components/ListaEncuentros";
import type {
  AgendaCompetencias,
  EstadoVistaCompetencias,
} from "../types/competencia.types";
import { formatearDia } from "../utils/competencias.fecha.utils";

/**
 * AgendaCompetenciasView - `ADM-13`, the encounters of a day.
 *
 * The agenda is the SAME operational source as the bracket and the detail
 * (`FL-11` paso 6): the encounter that opens here opens the SAME panel that
 * the bracket opens.
 *
 * It is TEMPORAL: the encounters of a day, with the local time of the
 * edition. A day without encounters is an empty agenda, never an error.
 */
export function AgendaCompetenciasView({
  estado = "sin-datos",
  agenda,
}: {
  estado?: EstadoVistaCompetencias;
  agenda?: AgendaCompetencias;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-13"
        title="Consultar la programación"
        description="Los encuentros programados de un día, agrupados por franja, con su horario, su duración y su marcador."
        meta={
          agenda
            ? [
                { etiqueta: "Día", valor: formatearDia(agenda.fecha) ?? "—" },
                {
                  etiqueta: "Encuentros",
                  valor: String(agenda.total),
                },
              ]
            : undefined
        }
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

      <AdminNotice title="Un día sin encuentros no es un error">
        La agenda es de solo lectura: no se reordena ni se edita desde aquí. Si
        no se indica un día, el backend resuelve el día actual y lo devuelve en
        la respuesta.
      </AdminNotice>

      <AdminPanel
        title="Agenda del día"
        description="Los encuentros del día seleccionado, agrupados por franja horaria."
      >
        {estado === "listo" ? (
          <ListaEncuentros encuentros={agenda?.encuentros ?? []} />
        ) : estado === "cargando" ? (
          <div role="status" aria-live="polite" className="flex flex-col gap-3">
            <span className="sr-only">Cargando la agenda…</span>
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : estado === "sin-permiso" ? (
          <ShellPermissionDenied title="No tienes permiso para ver esta sección" />
        ) : estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar la agenda"
            description="El servidor no devolvió los encuentros del día. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            accion={{ label: "Reintentar" }}
          />
        ) : (
          <AdminEmptyState
            icon={CalendarClock}
            title="Todavía no hay una agenda que mostrar"
            description="El servicio de administración de competencias todavía no está disponible en el backend, así que aquí no se dibuja ningún encuentro. Cuando lo esté, se podrá elegir el día y se mostrarán los encuentros con su horario y su marcador."
          />
        )}
      </AdminPanel>
    </div>
  );
}
