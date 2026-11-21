import {
  ArrowRight,
  ClipboardList,
  ShoppingBag,
  Sparkles,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
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
    <div className="flex flex-col gap-10 pb-10">
      <section className="relative left-1/2 w-screen -translate-x-1/2 border-b border-border bg-background px-4 py-10 sm:px-6 lg:py-12">
        <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-eyebrow-brand text-primary">
                Salesianos FEST 2026
              </p>
              <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                {nombre
                  ? `Hola, ${nombre.split(" ")[0] ?? nombre}`
                  : "Tu cuenta de responsable"}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                Aquí encontrarás el estado de tus inscripciones, los equipos y
                los pasos que faltan para completar la participación de tu
                promoción.
              </p>
            </div>
            <Button
              asChild
              size="lg"
              className="min-h-12 w-full rounded-full bg-accent px-6 text-sm font-semibold text-accent-foreground shadow-glow-brand transition-colors duration-(--motion-duration-fast) hover:bg-accent-muted sm:w-auto"
            >
              <Link href={RUTAS.cuenta.inscripcion}>
                <Sparkles className="size-4" aria-hidden="true" />
                Crear una inscripción
              </Link>
            </Button>
          </div>

          <div className="flex flex-col gap-3">
            <p className="text-eyebrow-brand text-primary/80">Cómo funciona</p>
            <PasosInscripcion className="gap-3 sm:grid-cols-2 xl:grid-cols-4" />
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl rounded-[var(--radius-xl)] border border-border bg-surface-elevated p-6 shadow-[var(--elevation-md)] sm:p-8">
        <div className="flex flex-col gap-1 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between sm:gap-6">
          <div>
            <p className="text-eyebrow-brand text-primary">Panel</p>
            <h2 className="mt-1 text-title-section text-foreground">
              Tus operaciones
            </h2>
            <p className="mt-1 max-w-measure text-caption text-muted-foreground">
              Cada acceso reúne el estado, lo que falta y el siguiente paso.
            </p>
          </div>
          <Link
            href={RUTAS.publico.inicio}
            className="inline-flex min-h-11 items-center gap-1 self-start text-sm font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:self-auto"
          >
            Ver el festival
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
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

        {/*
          Las dos operaciones de la cuenta son REJILLA desde 1024 (SH-02
          §1.1): a 360 y 768 se apilan a lo ancho y a 1024 y 1440 se leen de
          un vistazo. El grupo de `Item` es una columna: la rejilla la compone
          el contenedor, para que el hueco sea el de la retícula y no el del
          grupo.
        */}
        {estado !== "sin-permiso" && estado !== "error" ? (
          <div className="mt-5 grid gap-3 lg:grid-cols-2 lg:gap-4">
            <Item
              variant="outline"
              size="sm"
              asChild
              className="min-h-40 rounded-[var(--radius-lg)] border-border bg-background p-5 transition-colors duration-(--motion-duration-fast) hover:border-accent"
            >
              <Link href={RUTAS.cuenta.misInscripciones}>
                <ItemMedia
                  variant="icon"
                  className="size-11 rounded-[var(--radius-md)] bg-primary text-primary-foreground"
                >
                  <ClipboardList className="size-5" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle className="text-base font-semibold">
                    Inscripciones deportivas
                  </ItemTitle>
                  <ItemDescription className="max-w-sm">
                    El estado de cada registro, su paquete y las personas que
                    lleva.
                  </ItemDescription>
                </ItemContent>
                <ItemActions>
                  {hayResumen ? (
                    <span className="text-3xl font-semibold tabular-nums text-foreground">
                      {resumen?.inscripciones}
                      <span className="sr-only"> inscripciones</span>
                    </span>
                  ) : null}
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-primary transition-colors duration-(--motion-duration-fast) group-hover/item:bg-accent/10 group-hover/item:text-accent">
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </span>
                </ItemActions>
              </Link>
            </Item>

            <Item
              variant="outline"
              size="sm"
              asChild
              className="min-h-40 rounded-[var(--radius-lg)] border-border bg-background p-5 transition-colors duration-(--motion-duration-fast) hover:border-accent"
            >
              <Link href={RUTAS.cuenta.misCompras}>
                <ItemMedia
                  variant="icon"
                  className="size-11 rounded-[var(--radius-md)] bg-secondary text-secondary-foreground"
                >
                  <ShoppingBag className="size-5" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle className="text-base font-semibold">
                    Compras y pagos
                  </ItemTitle>
                  <ItemDescription className="max-w-sm">
                    Las compras de la edición, su estado de pago y su recogida.
                  </ItemDescription>
                </ItemContent>
                <ItemActions>
                  {hayResumen ? (
                    <span className="text-3xl font-semibold tabular-nums text-foreground">
                      {resumen?.compras}
                      <span className="sr-only"> compras</span>
                    </span>
                  ) : null}
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-primary transition-colors duration-(--motion-duration-fast) group-hover/item:bg-accent/10 group-hover/item:text-accent">
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </span>
                </ItemActions>
              </Link>
            </Item>

            <Item
              variant="outline"
              size="sm"
              asChild
              className="min-h-40 rounded-[var(--radius-lg)] border-border bg-background p-5 transition-colors duration-(--motion-duration-fast) hover:border-accent"
            >
              <Link href={RUTAS.cuenta.misPartidos}>
                <ItemMedia
                  variant="icon"
                  className="size-11 rounded-[var(--radius-md)] bg-accent text-accent-foreground"
                >
                  <Trophy className="size-5" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle className="text-base font-semibold">
                    Mis partidos
                  </ItemTitle>
                  <ItemDescription className="max-w-sm">
                    Los partidos de tus equipos: los que están en juego, los que
                    vienen y los últimos resultados.
                  </ItemDescription>
                </ItemContent>
                <ItemActions>
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-primary transition-colors duration-(--motion-duration-fast) group-hover/item:bg-accent/10 group-hover/item:text-accent">
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </span>
                </ItemActions>
              </Link>
            </Item>
          </div>
        ) : null}

        {estado === "sin-datos" ? (
          <RouteEmptyState
            icon={ClipboardList}
            className="mt-5 min-h-0 border-dashed bg-surface-recessed/40 py-8"
            title="Todavía no hay inscripciones para mostrar"
            description="Crea la primera inscripción de tu promoción y podrás seguir cada etapa desde este panel."
          />
        ) : null}
      </section>
    </div>
  );
}
