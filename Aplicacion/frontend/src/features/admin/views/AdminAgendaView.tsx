import { CalendarClock } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-13 - the agenda of a day.
 *
 * The agenda is TEMPORAL: the encounters of a day, grouped by time slot. A
 * day without encounters is an empty agenda, never an error.
 */
export function AdminAgendaView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-13"
        title="Consultar la programación"
        description="Los encuentros programados de un día, agrupados por franja, con su horario, su duración y su marcador."
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
        no se indica un día, el backend resuelve el día actual y lo devuelve
        en la respuesta.
      </AdminNotice>

      <AdminPanel
        title="Agenda del día"
        description="Los encuentros del día seleccionado, agrupados por franja horaria."
      >
        <AdminDataTable
          caption="Encuentros programados del día"
          columns={[
            { key: "franja", label: "Franja", numerico: true },
            { key: "competencia", label: "Competencia" },
            { key: "encuentro", label: "Encuentro" },
            { key: "estado", label: "Estado" },
            { key: "duracion", label: "Duración", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={CalendarClock}
              title="No hay encuentros para este día"
              description="La agenda del día se lee del servicio de administración. Cuando la integración esté disponible, se podrá elegir el día y se mostrarán los encuentros con su horario y su marcador."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
