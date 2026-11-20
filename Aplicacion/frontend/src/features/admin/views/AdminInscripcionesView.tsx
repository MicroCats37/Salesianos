import { ClipboardList } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-05 - the registrations of the edition.
 *
 * A registration is a commercial and a sporting fact at the same time: who
 * is responsible, what was bought, how many teams and people it carries and
 * how much of it is paid. The columns are ordered that way on purpose.
 */
export function AdminInscripcionesView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-05"
        title="Gestionar las inscripciones"
        description="Las inscripciones de la edición activa: quién las responde, qué paquete compraron, cuántas personas y equipos llevan y cuánto está pagado."
      />

      <AdminNotice title="Lectura, sin reescritura">
        La lista no valida, no rechaza ni libera cupos: publica el estado que
        calcula el backend. «Personas» y «Participaciones» son magnitudes
        distintas y la tabla las muestra por separado.
      </AdminNotice>

      <AdminPanel
        title="Inscripciones"
        description="Registros de la edición activa con sus agregados operativos."
      >
        <AdminDataTable
          caption="Inscripciones de la edición activa"
          columns={[
            { key: "responsable", label: "Responsable" },
            { key: "paquete", label: "Paquete" },
            { key: "estado", label: "Estado" },
            { key: "equipos", label: "Equipos", numerico: true },
            { key: "personas", label: "Personas", numerico: true },
            { key: "participaciones", label: "Participaciones", numerico: true },
            { key: "cupos", label: "Cupos pagados", numerico: true },
            { key: "monto", label: "Monto pagado", numerico: true },
            { key: "creada", label: "Creada", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={ClipboardList}
              title="Todavía no hay inscripciones cargadas"
              description="El listado de inscripciones se lee del servicio de administración. Cuando la integración esté disponible, aquí se verán los registros con su responsable, su paquete y su estado, con la búsqueda, los filtros y la paginación."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
