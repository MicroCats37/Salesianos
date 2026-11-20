import { UsersRound } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-07 - the team templates of the edition.
 *
 * A team is a roster under a discipline: it has a minimum and a maximum that
 * are two different facts, and a capacity verdict that only the backend can
 * give. The table never compares a roster with a threshold on its own.
 */
export function AdminEquiposView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-07"
        title="Buscar y gestionar equipos"
        description="Las plantillas del evento con su disciplina, su categoría, su completitud y el veredicto de capacidad de cada una."
      />

      <AdminNotice title="Dos hechos, no una fracción">
        El mínimo y el máximo deportivo son dos hechos independientes: el mínimo
        es lo que el equipo necesita para competir y el máximo es el tope duro
        de la disciplina. La capacidad y la completitud los deriva el servidor.
      </AdminNotice>

      <AdminPanel
        title="Equipos"
        description="Plantillas del evento con su inscripción de origen."
      >
        <AdminDataTable
          caption="Equipos de la edición"
          columns={[
            { key: "equipo", label: "Equipo" },
            { key: "disciplina", label: "Disciplina" },
            { key: "categoria", label: "Categoría" },
            { key: "inscripcion", label: "Inscripción" },
            { key: "plantilla", label: "Plantilla", numerico: true },
            { key: "capacidad", label: "Capacidad" },
            { key: "completitud", label: "Completitud" },
            { key: "estado", label: "Estado" },
            { key: "creada", label: "Creada", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={UsersRound}
              title="Todavía no hay equipos cargados"
              description="El listado de equipos se lee del servicio de administración. Cuando la integración esté disponible, aquí se listarán las plantillas con su disciplina y su veredicto de capacidad, con la búsqueda y los filtros."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
