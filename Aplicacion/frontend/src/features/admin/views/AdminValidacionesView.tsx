import { ScrollText } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-22 - the audit of what happened.
 *
 * This route is the memory of the edition: the entrances, the pickups and
 * the incidents, in the order they happened. It is the surface an operator
 * opens when something has to be explained.
 */
export function AdminValidacionesView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-22"
        title="Auditar ingresos, entregas e incidencias"
        description="El rastro de lo que ha pasado en la edición: los accesos a la fiesta, las recogidas de la tienda y las incidencias registradas."
      />

      <AdminNotice title="El registro no se reescribe">
        La auditoría es de solo lectura y conserva el orden de los hechos. Una
        incidencia se corrige con un asiento nuevo, nunca editando el anterior.
      </AdminNotice>

      <AdminPanel
        title="Bitácora"
        description="Los asientos del registro, del más reciente al más antiguo."
      >
        <AdminDataTable
          caption="Bitácora de ingresos, entregas e incidencias"
          columns={[
            { key: "momento", label: "Momento" },
            { key: "tipo", label: "Tipo" },
            { key: "resultado", label: "Resultado" },
            { key: "operador", label: "Operador" },
            { key: "referencia", label: "Referencia" },
          ]}
          vacio={
            <AdminEmptyState
              icon={ScrollText}
              title="Todavía no hay asientos en la bitácora"
              description="La bitácora se lee del servicio de administración. Cuando la integración esté disponible, aquí se listarán los ingresos, las entregas y las incidencias con su resultado y su responsable."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
