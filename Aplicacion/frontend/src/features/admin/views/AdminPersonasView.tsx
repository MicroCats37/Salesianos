import { Search } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-03 - the search of people by document.
 *
 * The operator arrives here with a document number in hand: the question is
 * always "who is this person and what are they part of", never "show me
 * everything". The search field is the primary action of the route.
 */
export function AdminPersonasView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-03"
        title="Buscar personas por documento"
        description="Localiza a una persona por su número de documento y comprueba en qué equipos, disciplinas e inscripciones aparece."
      />

      <AdminPanel
        title="Resultado de la búsqueda"
        description="La persona buscada, con su estado y las disciplinas en las que participa."
      >
        <AdminDataTable
          caption="Personas registradas en la edición"
          columns={[
            { key: "persona", label: "Persona" },
            { key: "documento", label: "Documento", identificador: true },
            { key: "estado", label: "Estado" },
            {
              key: "participaciones",
              label: "Participaciones",
              numerico: true,
            },
          ]}
          vacio={
            <AdminEmptyState
              icon={Search}
              title="Sin resultados"
              description="Escriba un documento en el buscador para localizar a una persona. La búsqueda se habilita cuando el servicio de personas esté conectado a esta superficie."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
