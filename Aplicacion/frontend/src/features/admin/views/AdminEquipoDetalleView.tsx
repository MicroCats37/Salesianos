import { UserRoundCheck } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-08 - the drilldown of a team.
 *
 * Two blocks: the roster that is already in the team and the candidates
 * that could still enter. Both come from the backend with its verdict, so
 * a person who cannot be assigned says why.
 */
export function AdminEquipoDetalleView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-08"
        title="Operar un equipo: plantilla y elegibilidad"
        description="La nómina de un equipo y las personas que todavía podrían entrar en él, con el motivo de cada bloqueo."
        meta={[{ etiqueta: "Equipo", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.equipos}>
              Volver a los equipos
            </Link>
          </Button>
        }
      />

      <AdminPanel
        title="Plantilla"
        description="Las personas que ya integran el equipo, con su rol y su estado."
      >
        <AdminDataTable
          caption="Nómina del equipo"
          columns={[
            { key: "persona", label: "Persona" },
            { key: "documento", label: "Documento" },
            { key: "rol", label: "Rol" },
            { key: "talla", label: "Talla" },
            { key: "estado", label: "Estado" },
          ]}
          vacio={
            <AdminEmptyState
              icon={UserRoundCheck}
              title="Sin plantilla en este equipo"
              description="Cuando el detalle esté conectado, aquí se listarán las personas del equipo con su rol, su talla y su estado dentro de la plantilla."
            />
          }
        />
      </AdminPanel>

      <AdminPanel
        title="Elegibilidad"
        description="Las personas que el backend considera asignables a este equipo y el motivo de las que no lo son."
      >
        <AdminEmptyState
          icon={UserRoundCheck}
          title="La elegibilidad la decide el backend"
          description="La lista de candidatos con su veredicto —asignable, motivo del bloqueo o disciplines ya cubiertas— llega del servidor. El navegador no pre-valida a nadie: reproduce el veredicto."
        />
      </AdminPanel>
    </div>
  );
}
