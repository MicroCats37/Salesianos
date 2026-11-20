import { Handshake } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-21 - the sponsors and their pieces.
 *
 * A sponsor is an ally with a name, a contact and a set of pieces: what
 * they contribute to the event and where their presence is published.
 */
export function AdminPatrocinadoresView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-21"
        title="Gestionar patrocinadores y sus piezas"
        description="Los aliados de la edición y las piezas que aportan: marca, presencia en la web y material impreso."
      />

      <AdminPanel
        title="Patrocinadores"
        description="Los aliados registrados, con su alias y su estado."
      >
        <AdminDataTable
          caption="Patrocinadores de la edición"
          columns={[
            { key: "patrocinador", label: "Patrocinador" },
            { key: "alias", label: "Alias", identificador: true },
            { key: "estado", label: "Estado" },
            { key: "piezas", label: "Piezas", numerico: true },
          ]}
          vacio={
            <AdminEmptyState
              icon={Handshake}
              title="Todavía no hay patrocinadores cargados"
              description="Los patrocinadores y sus piezas se leen del servicio de administración. Cuando la integración esté disponible, aquí se listarán con su alias y con la pieza que aporta cada uno."
            />
          }
        />
      </AdminPanel>

      <AdminPanel
        title="Piezas"
        description="Lo que aporta cada aliado y dónde se publica su presencia."
      >
        <AdminEmptyState
          icon={Handshake}
          title="Sin piezas publicadas"
          description="Las piezas son acuerdos con la organización: no se registran aquí sin que exista la operación que las respalde en el backend."
        />
      </AdminPanel>
    </div>
  );
}
