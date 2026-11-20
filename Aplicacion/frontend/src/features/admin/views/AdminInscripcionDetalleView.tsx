import { ClipboardCheck } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * ADM-06 - the drilldown of a registration.
 *
 * One registration carries six facts that never mix: the teams, the people,
 * the purchases, the assigned slots, the legal acceptances and the balance.
 * They are separate tabs because a reader of one of them never wants the
 * other five in the same viewport.
 *
 * The page is READ ONLY: it does not validate, does not reject, does not
 * release a slot and does not reassign a person.
 */
export function AdminInscripcionDetalleView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-06"
        title="Operar una inscripción"
        description="La ficha completa de una inscripción: equipos, participantes, compras, asignaciones de cupo, aceptaciones legales y saldo."
        meta={[{ etiqueta: "Inscripción", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.inscripciones}>
              Volver a las inscripciones
            </Link>
          </Button>
        }
      />

      <Tabs defaultValue="equipos" className="gap-4">
        <TabsList className="min-h-11 max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="equipos" className="min-h-11 flex-none">
            Equipos
          </TabsTrigger>
          <TabsTrigger value="participantes" className="min-h-11 flex-none">
            Participantes
          </TabsTrigger>
          <TabsTrigger value="compras" className="min-h-11 flex-none">
            Compras
          </TabsTrigger>
          <TabsTrigger value="asignaciones" className="min-h-11 flex-none">
            Asignaciones
          </TabsTrigger>
          <TabsTrigger value="aceptaciones" className="min-h-11 flex-none">
            Aceptaciones
          </TabsTrigger>
          <TabsTrigger value="saldo" className="min-h-11 flex-none">
            Saldo
          </TabsTrigger>
        </TabsList>

        <TabsContent value="equipos">
          <AdminPanel
            title="Equipos"
            description="Disciplina, categoría, plantilla y veredicto de capacidad de cada equipo."
          >
            <AdminDataTable
              caption="Equipos de la inscripción"
              columns={[
                { key: "equipo", label: "Equipo" },
                { key: "disciplina", label: "Disciplina" },
                { key: "categoria", label: "Categoría" },
                { key: "plantilla", label: "Plantilla" },
                { key: "capacidad", label: "Capacidad" },
                { key: "completitud", label: "Completitud" },
              ]}
              vacio={
                <AdminEmptyState
                  icon={ClipboardCheck}
                  title="Sin equipos en esta inscripción"
                  description="Cuando el detalle esté conectado, aquí se listarán los equipos con su disciplina, su plantilla y el veredicto de capacidad que calcula el backend."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="participantes">
          <AdminPanel
            title="Participantes"
            description="Las personas registradas en la inscripción y el estado de su cupo."
          >
            <AdminDataTable
              caption="Participantes de la inscripción"
              columns={[
                { key: "persona", label: "Persona" },
                { key: "documento", label: "Documento" },
                { key: "cupo", label: "Estado del cupo" },
                { key: "disciplinas", label: "Disciplinas" },
              ]}
              vacio={
                <AdminEmptyState
                  icon={ClipboardCheck}
                  title="Sin participantes en esta inscripción"
                  description="El detalle Trae a las personas registradas con el veredicto de pool y el motivo de bloqueo que devuelve el backend."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="compras">
          <AdminPanel
            title="Compras"
            description="Las compras de la inscripción, con su orden de pago y su estado."
          >
            <AdminDataTable
              caption="Compras de la inscripción"
              columns={[
                { key: "tipo", label: "Tipo" },
                { key: "cantidad", label: "Cantidad" },
                { key: "total", label: "Total" },
                { key: "compra", label: "Compra" },
                { key: "orden", label: "Orden" },
              ]}
              vacio={
                <AdminEmptyState
                  icon={ClipboardCheck}
                  title="Sin compras registradas"
                  description="Aquí aparecerán las compras de la inscripción con el estado de la compra y el de la orden de pago."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="asignaciones">
          <AdminPanel
            title="Asignaciones de cupo"
            description="Qué persona consume qué cupo pagado y en qué momento se liberó."
          >
            <AdminDataTable
              caption="Asignaciones de cupo de la inscripción"
              columns={[
                { key: "persona", label: "Persona" },
                { key: "estado", label: "Estado" },
                { key: "motivo", label: "Motivo" },
                { key: "liberada", label: "Liberada" },
              ]}
              vacio={
                <AdminEmptyState
                  icon={ClipboardCheck}
                  title="Sin asignaciones de cupo"
                  description="Las asignaciones son las que consumen el cupo pagado. El backend es la autoridad sobre su disponibilidad."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="aceptaciones">
          <AdminPanel
            title="Aceptaciones legales"
            description="Las declaraciones que la inscripción ha firmado y con qué versión."
          >
            <AdminDataTable
              caption="Aceptaciones legales de la inscripción"
              columns={[
                { key: "tipo", label: "Aceptación" },
                { key: "version", label: "Versión" },
                { key: "medio", label: "Medio" },
                { key: "aceptado", label: "Aceptado" },
              ]}
              vacio={
                <AdminEmptyState
                  icon={ClipboardCheck}
                  title="Sin aceptaciones registradas"
                  description="Aquí se listarán las declaraciones firmadas por la inscripción, con su versión y su medio."
                />
              }
            />
          </AdminPanel>
        </TabsContent>

        <TabsContent value="saldo">
          <AdminPanel
            title="Saldo de cupos"
            description="Cupos contratados, pagados, asignados y disponibles."
          >
            <AdminEmptyState
              icon={ClipboardCheck}
              title="El saldo se calcula en el backend"
              description="Los cuatro contadores —contratados, pagados, asignados y disponibles— se leen del detalle de la inscripción. El navegador no los recalcula: un cupo disponible aquí es un cupo que el backend ha liberado."
            />
          </AdminPanel>
        </TabsContent>
      </Tabs>
    </div>
  );
}
