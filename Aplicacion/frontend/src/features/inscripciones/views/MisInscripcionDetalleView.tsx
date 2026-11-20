"use client";

import { ArrowLeft, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RUTAS } from "@/lib/routes";
import { useInscripcionDetalle, useInscripcionPool } from "../hooks";
import { statusDeError } from "../utils/inscripcion.errores.utils";
import { PanelBeneficios } from "../components/PanelBeneficios";
import { PanelCompras } from "../components/PanelCompras";
import { PanelEquipos } from "../components/PanelEquipos";
import { PanelPool } from "../components/PanelPool";
import { SeccionParticipantes } from "../components/SeccionParticipantes";
import type { EstadoInscripcion } from "../types/inscripcion.types";

export interface MisInscripcionDetalleViewProps {
  /** The identifier of the registration, from the URL. */
  id: string;
}

/**
 * MisInscripcionDetalleView - ACCOUNT-03, the management of a registration.
 *
 * The responsible comes here to organise the teams, enrol the people and
 * see the state of the payment. The page is FIVE sections and a header: the
 * balance of the cupos, the teams, the people, the purchases and the
 * benefits.
 *
 * Every figure comes from the server. The page never subtracts cupos, never
 * decides an eligibility, never derives a price and never shows a state
 * that the backend did not publish.
 *
 * The two reads are REAL (`RT-IN-02` and `RT-IN-03`) and the page shows the
 * message of the server verbatim when one of them fails.
 */
export function MisInscripcionDetalleView(props: MisInscripcionDetalleViewProps) {
  const detalle = useInscripcionDetalle(props.id);
  const pool = useInscripcionPool(props.id);

  const errorDetalle = detalle.error;

  /**
   * The state of the route.
   *
   * The frontend branches on the HTTP STATUS and never on the machine code
   * of the error: a 403 means that this account does not own the
   * registration, and anything else is a recoverable failure.
   */
  const estado: EstadoInscripcion = errorDetalle
    ? statusDeError(errorDetalle) === 403
      ? "sin-permiso"
      : "error"
    : detalle.data
      ? "listo"
      : "sin-datos";

  if (estado === "sin-permiso") {
    return (
      <div className="flex flex-col gap-6">
        <RouteHero
          pageId="ACCOUNT-03"
          title="Tu inscripción"
          description="Esta inscripción no se puede abrir con tu cuenta."
        />
        <RouteEmptyState
          icon={TriangleAlert}
          title="Tu cuenta no tiene acceso a esta inscripción"
          description="Solo el responsable de la inscripción y los administradores autorizados pueden verla. Si crees que es un error, escríbenos y lo revisamos."
        />
      </div>
    );
  }

  if (estado === "error") {
    return (
      <div className="flex flex-col gap-6">
        <RouteHero
          pageId="ACCOUNT-03"
          title="Tu inscripción"
          description="No pudimos leer los datos de esta inscripción."
        />
        <Alert className="border-destructive/45 bg-destructive/10">
          <TriangleAlert
            className="size-4 text-destructive"
            aria-hidden="true"
          />
          <AlertTitle className="text-foreground">
            No pudimos leer tu inscripción
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            {errorDetalle?.message ??
              "El servicio de inscripciones no respondió. Vuelve a intentarlo en unos segundos."}
          </AlertDescription>
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => void detalle.refetch()}
              className="min-h-11"
            >
              Reintentar
            </Button>
          </div>
        </Alert>
      </div>
    );
  }

  const inscripcion = detalle.data ?? null;

  if (estado !== "listo" || !inscripcion) {
    return (
      <div className="flex flex-col gap-6">
        <RouteHero
          pageId="ACCOUNT-03"
          title="Tu inscripción"
          description="Estamos leyendo los datos de esta inscripción."
        />
        <RouteEmptyState
          icon={TriangleAlert}
          title="No hay datos de esta inscripción todavía"
          description="El detalle de una inscripción lo publica el servidor. En cuanto esté disponible, aquí aparecerá el balance de cupos, los equipos, las personas, las compras y los beneficios."
        />
      </div>
    );
  }

  const poolInscripcion = pool.data ?? null;

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="ACCOUNT-03"
        title={inscripcion.paquete_nombre}
        description={inscripcion.edicion_nombre}
        facts={[
          { label: "Estado", value: inscripcion.estado },
          { label: "Referencia", value: inscripcion.referencia },
        ]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.cuenta.misInscripciones}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a mis inscripciones
            </Link>
          </Button>
        }
      />

      <Tabs defaultValue="pool" className="gap-4">
        <TabsList className="flex min-h-11 w-full flex-wrap justify-start gap-1">
          <TabsTrigger value="pool" className="min-h-11">
            Cupos
          </TabsTrigger>
          <TabsTrigger value="equipos" className="min-h-11">
            Equipos
          </TabsTrigger>
          <TabsTrigger value="participantes" className="min-h-11">
            Personas
          </TabsTrigger>
          <TabsTrigger value="compras" className="min-h-11">
            Compras
          </TabsTrigger>
          <TabsTrigger value="beneficios" className="min-h-11">
            Beneficios
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pool">
          <PanelPool pool={poolInscripcion} />
        </TabsContent>

        <TabsContent value="equipos">
          <PanelEquipos equipos={inscripcion.equipos} />
        </TabsContent>

        <TabsContent value="participantes">
          <SeccionParticipantes
            inscripcionId={inscripcion.id}
            equipos={inscripcion.equipos}
            participaciones={poolInscripcion?.participaciones ?? []}
          />
        </TabsContent>

        <TabsContent value="compras">
          {/*
            The target backend publishes NO route that LISTS the purchases of
            a registration: the initial one comes with the alta and every
            expansion with its own answer (`RT-CM-01`). The section says so
            instead of showing an empty list that would read as "there are
            no purchases".
          */}
          <PanelCompras compras={null} />
        </TabsContent>

        <TabsContent value="beneficios">
          {/*
            `BeneficioConcedido` exists in the domain of DOM-02, but NO
            presenter of the target backend publishes it: the section is an
            honest empty until a route exists.
          */}
          <PanelBeneficios beneficios={null} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
