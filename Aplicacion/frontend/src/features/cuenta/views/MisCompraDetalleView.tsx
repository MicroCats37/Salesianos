import { ArrowLeft, ArrowRight, QrCode, Receipt } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";
import { EstadoIndeterminado, VeredictoEstado } from "../components";
import { etiquetaOrigen } from "../components/ListaCompras";
import type { CompraDetalle, EstadoVista } from "../types/cuenta.types";

export interface MisCompraDetalleViewProps {
  /** The identifier of the purchase, taken from the URL. */
  id: string;
  /** The state of the detail. */
  estado?: EstadoVista;
  /** The purchase, when the service answered. */
  compra?: CompraDetalle;
}

/**
 * ACCOUNT-05 - the detail of a purchase.
 *
 * Four things, in the order the reader needs them: what was bought, whether
 * the payment is confirmed, what was obtained and where to go next.
 *
 * The QR is NOT rendered here: the code is a bearer credential and it is
 * delivered by the module that owns it, never painted in a list. Neither the
 * provider state nor its machine codes nor the provider tokens appear here
 * (`GOV-02-RB-01d`).
 */
export function MisCompraDetalleView({
  id,
  estado = "sin-datos",
  compra,
}: MisCompraDetalleViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="ACCOUNT-05"
        tone="hero"
        title="Tu compra"
        description="El estado del pago, el detalle de la compra y el destino de la recogida, con la evidencia que registra el backend."
        facts={[{ label: "Compra", value: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.cuenta.misCompras}>
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a mis compras
            </Link>
          </Button>
        }
      />

      {estado === "sin-permiso" ? (
        <ShellPermissionDenied
          title="Esta compra no está disponible para tu cuenta"
          description="Tu cuenta no tiene acceso a esta compra. Si crees que es un error, contacta con la organización del evento."
          className="border-border bg-surface-raised"
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos cargar esta compra"
          description="No pudimos leer el detalle en este momento. Vuelve a intentarlo en unos segundos."
          accion={{
            label: "Volver a mis compras",
            href: RUTAS.cuenta.misCompras,
          }}
        />
      ) : null}

      {estado === "sin-datos" ? (
        <>
          <RouteEmptyState
            icon={Receipt}
            title="Todavía no hay una compra que mostrar"
            description="El detalle de la compra llega del servicio de la cuenta con su estado de compra, su estado de orden y su evidencia de pago. La interfaz no afirma un pago que el proveedor no ha confirmado."
          />
          <RouteEmptyState
            icon={QrCode}
            title="La recogida se confirmará con el personal del evento"
            description="Si la compra incluye una recogida en el punto de control, el personal la confirmará allí con el código del pase. El código no se publica en esta pantalla."
          />
        </>
      ) : null}

      {estado === "listo" && compra ? (
        <>
          {compra.veredicto.rol === "atencion" ? (
            <EstadoIndeterminado
              titulo="Pago confirmado, pendiente de activación"
              descripcion="El cobro está confirmado, pero el derecho todavía no se ha habilitado. No vuelvas a pagar: la activación la resuelve el servidor y el estado se actualiza solo."
              accion={{
                etiqueta: "Volver a mis compras",
                href: RUTAS.cuenta.misCompras,
              }}
            />
          ) : null}

          <section className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-5 shadow-[var(--elevation-sm)]">
            <h2 className="text-section-title text-foreground">
              Qué compraste
            </h2>

            <dl className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Concepto</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {compra.concepto}
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Origen</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {etiquetaOrigen(compra.origen)}
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Importe</dt>
                <dd className="text-sm font-semibold tabular-nums text-foreground">
                  {compra.moneda} {compra.monto}
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Fecha</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {compra.fecha}
                </dd>
              </div>
            </dl>

            <div className="flex flex-col gap-1.5 border-t border-border pt-4">
              <span className="text-caption text-muted-foreground">
                Estado del pago
              </span>
              <VeredictoEstado veredicto={compra.veredicto} conDescripcion />
            </div>
          </section>

          <section className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-5 shadow-[var(--elevation-sm)]">
            <h2 className="text-section-title text-foreground">
              Qué obtuviste
            </h2>
            {compra.derechos.length > 0 ? (
              <ul className="flex flex-col gap-2">
                {compra.derechos.map((derecho) => (
                  <li
                    key={derecho.etiqueta}
                    className="text-sm text-foreground"
                  >
                    {derecho.etiqueta}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                Todavía no hay derechos habilitados para esta compra.
              </p>
            )}
          </section>

          {compra.ruta_origen ? (
            <div className="flex flex-col gap-2">
              <h2 className="text-section-title text-foreground">
                Siguiente paso
              </h2>
              <Button asChild className="min-h-11 w-fit">
                <Link href={compra.ruta_origen}>
                  Ir a {etiquetaOrigen(compra.origen).toLowerCase()}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
            </div>
          ) : null}

          <RouteEmptyState
            icon={QrCode}
            title="La recogida se confirmará con el personal del evento"
            description="Si la compra incluye una recogida en el punto de control, el personal la confirmará allí con el código del pase. El código no se publica en esta pantalla."
          />
        </>
      ) : null}
    </div>
  );
}
