import { CalendarDays } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-02 - the editions of the festival.
 *
 * An edition is the container of everything else: it decides which modules
 * run, from which date and until when the event accepts changes. It is the
 * first route an operator opens when a new edition is prepared.
 */
export function AdminEdicionesView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-02"
        title="Crear y publicar ediciones"
        description="Las ediciones del festival: qué módulos quedan habilitados en cada una, desde cuándo corre cada módulo y hasta cuándo se admiten cambios."
      />

      <AdminNotice title="Alta y publicación">
        El alta de una edición y su publicación se habilitan cuando el
        servicio de administración exponga la operación. Esta pantalla es de
        lectura: no inventa un formulario que no tenga destino.
      </AdminNotice>

      <AdminPanel
        title="Ediciones"
        description="Las ediciones publicadas, con sus módulos habilitados y su ventana de fechas."
      >
        <AdminDataTable
          caption="Ediciones del festival"
          columns={[
            { key: "edicion", label: "Edición" },
            { key: "modulos", label: "Módulos habilitados" },
            { key: "desde", label: "Desde" },
            { key: "hasta", label: "Hasta" },
            { key: "estado", label: "Estado" },
          ]}
          vacio={
            <AdminEmptyState
              icon={CalendarDays}
              title="Todavía no hay ediciones"
              description="Las ediciones se leen del catálogo de eventos del backend. Cuando la integración esté disponible, aquí se listarán con sus módulos y sus fechas, y el alta se habilitará sobre la misma lista."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
