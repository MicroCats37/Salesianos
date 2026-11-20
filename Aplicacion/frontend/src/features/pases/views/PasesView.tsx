import { CreditCard, Ticket, UserRound } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { CatalogoPases } from "../components/CatalogoPases";
import type {
  CatalogoPases as CatalogoPasesModelo,
  EstadoVistaPases,
  EnviarCompraPase,
  VeredictoPago,
} from "../types/pase.types";

/** The three steps of the purchase, told before the catalogue. */
const PASOS = [
  {
    titulo: "Elige tu pase",
    detalle: "El pase es nominativo: cada entrada pertenece a una persona.",
    Icono: Ticket,
  },
  {
    titulo: "Completa el pago",
    detalle: "El precio y la moneda los fija el servidor en el momento del pago.",
    Icono: CreditCard,
  },
  {
    titulo: "Asigna los beneficiarios",
    detalle: "Después del pago, el enlace permite elegir quién usa cada pase.",
    Icono: UserRound,
  },
] as const;

export interface PasesViewProps {
  /** The state of the catalogue. */
  estado?: EstadoVistaPases;
  /** The catalogue of the edition, when it is available. */
  catalogo?: CatalogoPasesModelo;
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the
   * server chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The transport of the purchase. */
  enviar?: EnviarCompraPase;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}
/**
 * PASS-01 - the purchase of the party passes.
 *
 * The pass is NOT a branch of the sports registration: it gives access to
 * the party and it says so. The three steps of the flow are told before the
 * catalogue, because the visitor arrives here with the question "what is
 * this" before "how much does it cost".
 *
 * The catalogue is not connected yet, so the default state is the HONEST
 * one: the route says that the catalogue is not available instead of
 * drawing an example catalogue (`FR-08` 1.4).
 */
export function PasesView({
  estado = "sin-datos",
  catalogo,
  pago,
  mensajeError,
  enviar,
  reintentar,
}: PasesViewProps) {
  const sinPases = estado === "listo" && (catalogo?.pases.length ?? 0) === 0;

  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="PASS-01"
        title="Comprar un pase de fiesta"
        description="El pase da acceso nominativo a la fiesta, sin inscripción deportiva. Elige el pase, confirma la cantidad y completa el pago: el precio lo fija el servidor."
        tone="band"
      />

      <section className="flex flex-col gap-4">
        <h2 className="text-section-title text-foreground">
          Cómo funciona la compra
        </h2>
        <ol className="grid gap-3 sm:grid-cols-3">
          {PASOS.map((paso, indice) => {
            const Icono = paso.Icono;

            return (
              <li
                key={paso.titulo}
                className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-card p-4"
              >
                <span className="flex items-center gap-2">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Icono className="size-4" aria-hidden="true" />
                    <span className="sr-only">Paso {indice + 1}</span>
                  </span>
                  <span className="text-sm font-bold text-foreground">
                    {paso.titulo}
                  </span>
                </span>
                <p className="text-caption text-muted-foreground">
                  {paso.detalle}
                </p>
              </li>
            );
          })}
        </ol>
      </section>
      {estado === "sin-permiso" ? (
        <ShellPermissionDenied
          title="No podemos mostrarte los pases"
          description="Esta zona del festival no está disponible para ti ahora mismo. Si crees que es un error, contacta con la organización del evento."
          className="border-border bg-surface-raised"
        />
      ) : null}

      {estado === "cargando" ? (
        <ShellPendingState
          title="Cargando el catálogo de pases"
          description="Estamos leyendo los pases y los precios de esta edición."
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar el catálogo de pases"
          description={
            mensajeError ??
            "No pudimos leer los pases de esta edición en este momento. Vuelve a intentarlo en unos segundos."
          }
          accion={reintentar ? { label: "Reintentar", onClick: reintentar } : undefined}
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={Ticket}
          title="El catálogo de pases todavía no está disponible"
          description="Los pases y sus precios los publica el catálogo del backend, con un precio por preventa y otro por venta regular. Esta sección se completará con esa fuente; hasta entonces no se muestra ningún precio que el servidor no haya confirmado."
        />
      ) : null}

      {sinPases ? (
        <RouteEmptyState
          icon={Ticket}
          title="No hay pases a la venta en esta edición"
          description="La edición no publica ningún pase todavía. Vuelve más tarde o mira el programa del festival."
        />
      ) : null}

      {estado === "listo" && !sinPases && catalogo ? (
        <CatalogoPases pases={catalogo.pases} pago={pago} enviar={enviar} />
      ) : null}
    </div>
  );
}