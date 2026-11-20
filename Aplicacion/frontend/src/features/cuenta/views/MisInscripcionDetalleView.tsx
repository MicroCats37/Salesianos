import { ArrowLeft, Users, Wallet } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RUTAS } from "@/lib/routes";

/**
 * ACCOUNT-03 - the drilldown of a registration of the responsible.
 *
 * The three blocks are the three things the responsible does with her
 * registration: organise the teams, enrol the people and pay. They never
 * appear together: an operator of the pool does not need the balance.
 */
export function MisInscripcionDetalleView({ id }: { id: string }) {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="ACCOUNT-03"
        tone="hero"
        title="Tu inscripción"
        description="Los equipos de la promoción, las personas que esperan cupo y el estado del pago, con los contadores que calcula el servidor."
        facts={[{ label: "Inscripción", value: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.cuenta.misInscripciones}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a mis inscripciones
            </Link>
          </Button>
        }
      />

      <Tabs defaultValue="equipos" className="gap-4">
        <TabsList className="min-h-11 max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="equipos" className="min-h-11 flex-none">
            Equipos
          </TabsTrigger>
          <TabsTrigger value="pool" className="min-h-11 flex-none">
            Personas
          </TabsTrigger>
          <TabsTrigger value="pago" className="min-h-11 flex-none">
            Pago
          </TabsTrigger>
        </TabsList>

        <TabsContent value="equipos">
          <RouteEmptyState
            icon={Users}
            title="Todavía no hay equipos en esta inscripción"
            description="La plantilla de la promoción se lee del servicio de inscripciones. Cuando la integración esté disponible, aquí se listarán los equipos con su disciplina, su categoría y su número de jugadores."
          />
        </TabsContent>

        <TabsContent value="pool">
          <RouteEmptyState
            icon={Users}
            title="Todavía no hay personas en el pool"
            description="El pool es la lista de personas que esperan cupo. El backend decide quién puede entrar a cada equipo y por qué: la interfaz no lo pre-valida."
          />
        </TabsContent>

        <TabsContent value="pago">
          <RouteEmptyState
            icon={Wallet}
            title="El estado del pago lo decide el servidor"
            description="La compra, la orden de pago y su evidencia de pago llegan del backend. La interfaz no afirma un pago que no ha confirmado el proveedor."
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
