import { Trophy } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
  AdminSubnav,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-10 - the competitions of the edition.
 *
 * The area of competitions is split in three pages of its own: the list, the
 * agenda of a day and the bracket of a competition. The subnavigation says
 * where the operator is before the content starts.
 */
export function AdminCompetenciasView() {
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

      <AdminPanel
        title="Competencias"
        description="Las competencias publicadas, con sus equipos y sus encuentros."
      >
        <AdminDataTable
          caption="Competencias de la edición"
          columns={[
            { key: "competencia", label: "Competencia" },
            { key: "estado", label: "Estado" },
            { key: "equipos", label: "Equipos", numerico: true },
            { key: "encuentros", label: "Encuentros", numerico: true },
            { key: "acciones", label: "Acciones" },
          ]}
          vacio={
            <AdminEmptyState
              icon={Trophy}
              title="Todavía no hay competencias cargadas"
              description="El listado de competencias se lee del servicio de administración. Cuando la integración esté disponible, aquí se listarán con sus contadores, con su enlace al detalle y con su enlace al cuadro."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
