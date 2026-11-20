import { Users } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";

/**
 * ADM-09 - people and participations.
 *
 * Two surfaces that are never reconciled in the browser: the people who are
 * registered and the rows of the roster. A paid slot enables a person in
 * every contracted discipline, so "people" and "participations" are
 * different magnitudes by construction.
 */
export function AdminParticipantesView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-09"
        title="Buscar personas y participaciones"
        description="Dos superficies distintas: las personas registradas en el evento y las filas de roster que cada disciplina ha cerrado."
      />

      <AdminNotice title="Dos magnitudes, no una">
        Las dos listas nunca se reconcilian en el navegador. Un cupo pagado
        habilita a una persona en todas las disciplinas contratadas, así que
        «personas» y «participaciones» son recuentos distintos por construcción.
      </AdminNotice>

      <Tabs defaultValue="personas" className="gap-4">
        <TabsList className="min-h-11 max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="personas" className="min-h-11 flex-none">
            Personas registradas
          </TabsTrigger>
          <TabsTrigger value="participaciones" className="min-h-11 flex-none">
            Participaciones
          </TabsTrigger>
        </TabsList>

        <TabsContent value="personas">
          <AdminPanel
            title="Personas registradas"
            description="El pool del evento: quién está registrado y en qué estado queda su cupo."
          >
            <AdminDataTable
              caption="Personas registradas en el evento"
              columns={[
                { key: "persona", label: "Persona" },
                { key: "vinculo", label: "Vínculo" },
                { key: "cupo", label: "Estado del cupo" },
                { key: "disciplinas", label: "Disciplinas" },
                { key: "registrada", label: "Registrada", numerico: true },
              ]}
              vacio={
                <AdminEmptyState
                  icon={Users}
                  title="Todavía no hay personas cargadas"
                  description="El pool de personas se lee del servicio de administración. Cuando la integración esté disponible, aquí se listará cada persona con su veredicto de cupo y el motivo de su bloqueo."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="participaciones">
          <AdminPanel
            title="Participaciones por disciplina"
            description="Las filas de roster: quién juega en qué equipo, con qué rol y en qué estado."
          >
            <AdminDataTable
              caption="Participaciones por disciplina"
              columns={[
                { key: "persona", label: "Persona" },
                { key: "equipo", label: "Equipo" },
                { key: "disciplina", label: "Disciplina" },
                { key: "rol", label: "Rol" },
                { key: "talla", label: "Talla" },
                { key: "roster", label: "Fila de roster" },
                { key: "creada", label: "Creada", numerico: true },
              ]}
              vacio={
                <AdminEmptyState
                  icon={Users}
                  title="Todavía no hay participaciones cargadas"
                  description="Las participaciones se leen del servicio de administración, con su filtro por disciplina, por rol y por estado."
                />
              }
            />
          </AdminPanel>
        </TabsContent>
      </Tabs>
    </div>
  );
}
