import { Lock, PackageSearch } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { ShellErrorState } from "@/components/shell/ShellState";
import { EstadoPagoTienda } from "../components/EstadoPagoTienda";
import type {
  EstadoDeclarado,
  EstadoVistaTienda,
  SeguimientoPedido,
  VeredictoPago,
} from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";

export interface PedidoSeguimientoViewProps {
  /** The private token of the link. It IS the credential. */
  token: string;
  /** The state of the order. */
  estado?: EstadoVistaTienda;
  /** The order, when the link opens it. */
  pedido?: SeguimientoPedido;
  /** The payment verdict, resolved by the adapter. */
  pago?: VeredictoPago;
  /** The delivery state, resolved by the adapter. */
  entrega?: EstadoDeclarado;
}

/**
 * SHOP-03 - the state of an order and its pickup.
 *
 * The route is reached with a token in the URL: the token IS the credential
 * and it opens exactly one order. The visitor does not need a session, and
 * the page never shows an order that the token does not open.
 *
 * **The payment state and the delivery state are TWO different facts and TWO
 * different lines** (`RN-M07`, `QA-M04`): a paid order that has not been
 * delivered never reads as "delivered".
 */
export function PedidoSeguimientoView({
  token,
  estado = "sin-datos",
  pedido,
  pago,
  entrega,
}: PedidoSeguimientoViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SHOP-03"
        title="Estado de tu pedido"
        description="El pedido, su estado de pago y su recogida. El enlace que recibiste abre únicamente este pedido."
        facts={[{ label: "Acceso", value: `${token.slice(0, 8)}...` }]}
      />

      {estado === "sin-permiso" ? (
        <Alert>
          <Lock className="size-4" aria-hidden="true" />
          <AlertTitle>No pudimos abrir este pedido</AlertTitle>
          <AlertDescription>
            El enlace puede haber caducado o no corresponde a este pedido. Si
            lo has perdido, puedes pedir un enlace nuevo para recuperarlo.
          </AlertDescription>
        </Alert>
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos comprobar tu enlace"
          description="No pudimos comprobar el enlace en este momento. Vuelve a intentarlo en unos segundos."
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={PackageSearch}
          title="Este pedido todavía no se puede mostrar"
          description="El servicio de pedidos de la tienda todavía no está publicado, así que aquí no se puede abrir ningún pedido. En cuanto lo esté, este enlace abrirá el pedido con su estado de compra, su estado de orden y su evidencia de pago. La interfaz no afirma un pago que el proveedor no ha confirmado."
        />
      ) : null}

      {estado === "listo" && pedido ? (
        <>
          <section
            aria-labelledby="estados-pedido-titulo"
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <h2
              id="estados-pedido-titulo"
              className="text-section-title text-foreground"
            >
              Estado del pedido
            </h2>

            <dl className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted-foreground">Pago</dt>
                <dd>
                  {pago ? (
                    <EstadoPagoTienda veredicto={pago} />
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      Todavía no hay un veredicto de pago.
                    </span>
                  )}
                </dd>
              </div>

              <div className="flex flex-col gap-1">
                <dt className="text-caption text-muted-foreground">Entrega</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {entrega ? entrega.etiqueta : "Sin estado de entrega"}
                </dd>
              </div>
            </dl>

            <p className="text-caption text-muted-foreground">
              Pagar el pedido no lo entrega: la recogida se confirma en el
              punto de control del evento.
            </p>
          </section>

          <section
            aria-labelledby="productos-pedido-titulo"
            className="flex flex-col gap-3"
          >
            <h2
              id="productos-pedido-titulo"
              className="text-section-title text-foreground"
            >
              Productos
            </h2>

            <ul className="flex flex-col gap-2">
              {pedido.lineas.map((linea) => (
                <li
                  key={`${linea.concepto_id}-${linea.tipo_concepto}`}
                  className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised px-3 py-2"
                >
                  <span className="text-sm text-foreground">
                    {`${linea.cantidad} x ${linea.concepto_nombre}`}
                  </span>
                  <span className="text-sm font-semibold tabular-nums text-foreground">
                    {formatearMonto(linea.subtotal, pedido.moneda)}
                  </span>
                </li>
              ))}
            </ul>

            <p className="text-sm font-semibold tabular-nums text-foreground">
              {`Total: ${formatearMonto(pedido.total, pedido.moneda)}`}
            </p>
          </section>
        </>
      ) : null}
    </div>
  );
}
