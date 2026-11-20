import { ArrowRight, ClipboardList, ShoppingBag, Sparkles } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { ShellErrorState } from "@/components/shell/ShellState";
import { ShellPermissionDenied } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import { RUTAS } from "@/lib/routes";
import { PasosInscripcion } from "../components/PasosInscripcion";
import type { EstadoVista, ResumenCuenta } from "../types/cuenta.types";

export interface MiCuentaViewProps {
  /** The name of the responsible, read from the session on the server. */
  nombre?: string;
  /** The state of the account summary. */
  estado?: EstadoVista;
  /** The counters, when the summary is available. */
  resumen?: ResumenCuenta;
}

/**
 * ACCOUNT-01 - the hub of the account area.
 *
 * The responsible has two destinations and this is the hub: it says where
 * the registration is, offers the next step and links to the two lists.
 *
 * The summary is a SUMMARY and not a table of the whole system
 * (`frontend/02` ACCOUNT-01): two counters, each with its label, each one
 * a link to the list it counts.
 */
export function MiCuentaView({
  nombre,
  estado = "sin-datos",
  resumen,
}: MiCuentaViewProps) {
  const hayResumen = estado === "listo" && Boolean(resumen);

  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="ACCOUNT-01"
        title={
          nombre ? `Hola, ${nombre.split(" ")[0] ?? nombre}` : "Tu cuenta de responsable"
        }
        description="Desde aquí sigues tus inscripciones, tus compras y el siguiente paso de cada una. El comité valida cada inscripción antes de que se active."
        actions={
          <Button asChild size="lg" className="min-h-11">
            <Link href={RUTAS.cuenta.inscripcion}>
              <Sparkles className="size-4" aria-hidden="true" />
              Crear una inscripción
            </Link>
          </Button>
        }
      />

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-section-title text-foreground">Tus operaciones</h2>
          <p className="max-w-measure text-caption text-muted-foreground">
            Las dos listas de la cuenta, con el estado que calcula el servidor.
          </p>
        </div>

        {estado === "sin-permiso" ? (
          <ShellPermissionDenied
            title="No podemos leer el resumen de tu cuenta"
            className="border-border bg-surface-raised"
          />
        ) : null}

        {estado === "error" ? (
          <ShellErrorState
            title="No pudimos leer el resumen de tu cuenta"
            description="Vuelve a intentarlo en unos segundos. Tus inscripciones y tus compras siguen guardadas."
          />
        ) : null}

        {estado !== "sin-permiso" && estado !== "error" ? (
          <ItemGroup className="gap-2">
            <Item
              variant="outline"
              size="sm"
              asChild
              className="transition-all duration-(--motion-duration-base) hover:border-primary/40 hover:shadow-[var(--elevation-md)]"
            >
              <Link href={RUTAS.cuenta.misInscripciones}>
                <ItemMedia variant="icon">
                  <ClipboardList className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Mis inscripciones</ItemTitle>
                  <ItemDescription>
                    El estado de cada registro, su paquete y las personas que
                    lleva.
                  </ItemDescription>
                </ItemContent>
                <ItemActions>
                  {hayResumen ? (
                    <span className="text-2xl font-bold tabular-nums text-primary">
                      {resumen?.inscripciones}
                      <span className="sr-only"> inscripciones</span>
                    </span>
                  ) : null}
                  <ArrowRight
                    className="size-4 shrink-0 text-muted-foreground transition-transform duration-(--motion-duration-fast) group-hover/item:translate-x-1"
                    aria-hidden="true"
                  />
                </ItemActions>
              </Link>
            </Item>

            <Item
              variant="outline"
              size="sm"
              asChild
              className="transition-all duration-(--motion-duration-base) hover:border-primary/40 hover:shadow-[var(--elevation-md)]"
            >
              <Link href={RUTAS.cuenta.misCompras}>
                <ItemMedia variant="icon">
                  <ShoppingBag className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Mis compras</ItemTitle>
                  <ItemDescription>
                    Las compras de la edición, su estado de pago y su recogida.
                  </ItemDescription>
                </ItemContent>
                <ItemActions>
                  {hayResumen ? (
                    <span className="text-2xl font-bold tabular-nums text-primary">
                      {resumen?.compras}
                      <span className="sr-only"> compras</span>
                    </span>
                  ) : null}
                  <ArrowRight
                    className="size-4 shrink-0 text-muted-foreground transition-transform duration-(--motion-duration-fast) group-hover/item:translate-x-1"
                    aria-hidden="true"
                  />
                </ItemActions>
              </Link>
            </Item>
          </ItemGroup>
        ) : null}

        {estado === "sin-datos" ? (
          <RouteEmptyState
            icon={ClipboardList}
            title="Todavía no hay un resumen de la cuenta"
            description="El resumen reúne tus inscripciones, sus pasos y sus pagos en un vistazo. Se compondrá cuando el servicio de la cuenta esté conectado; mientras tanto, las dos listas de arriba muestran lo mismo."
          />
        ) : null}
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-section-title text-foreground">
            Cómo avanza una inscripción
          </h2>
          <p className="max-w-measure text-caption text-muted-foreground">
            Los cuatro pasos son los mismos para todas las promociones: lo
            único que cambia es en cuál de ellos está la tuya.
          </p>
        </div>
        <PasosInscripcion />
      </section>
    </div>
  );
}
