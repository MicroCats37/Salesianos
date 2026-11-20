import { Ticket } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-15 - the party passes and the courtesy passes.
 *
 * A pass is a nominative right: it belongs to a person, it can be revoked,
 * and it carries its own payment evidence. The revenue of the passes is
 * deliberately kept apart from the sport metrics of the edition.
 */
export function AdminPasesView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-15"
        title="Gestionar pases de fiesta y cortesías"
        description="Los pases de la fiesta y las cortesías de la organización, con su titular, su estado y su evidencia de pago."
      />

      <AdminNotice title="Ingreso separado del deporte">
        El ingreso de los pases no se mezcla con las métricas deportivas de
        la edición: una venta de pases no es una inscripción y no ocupa
        cupo.
      </AdminNotice>

      <AdminPanel
        title="Pases"
        description="Los pases emitidos, con su titular y su estado."
      >
        <AdminDataTable
          caption="Pases de fiesta y cortesías"
          columns={[
            { key: "titular", label: "Titular" },
            { key: "documento", label: "Documento", identificador: true },
            { key: "tipo", label: "Tipo" },
            { key: "estado", label: "Estado" },
            { key: "accesos", label: "Accesos", numerico: true },
            { key: "emitido", label: "Emitido", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={Ticket}
              title="Todavía no hay pases cargados"
              description="Los pases y sus beneficiarios se leen del servicio de administración. Cuando la integración esté disponible, aquí se listarán con su titular, su tipo y su estado, con el filtro por estado de pago."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
