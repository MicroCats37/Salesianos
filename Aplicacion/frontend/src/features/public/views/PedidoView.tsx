import { PackageCheck, PackageSearch } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";

/**
 * SHOP-03 - the state of an order and its pickup.
 *
 * The route is reached with a token in the URL: the token IS the credential
 * and it opens exactly one order. The visitor does not need a session, and
 * the page never shows an order that the token does not open.
 */
export function PedidoView({ token }: { token: string }) {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="SHOP-03"
        title="Estado de tu pedido"
        description="El pedido, su estado de pago y su recogida. El enlace que recibiste abre únicamente este pedido."
        facts={[{ label: "Acceso", value: `${token.slice(0, 8)}…` }]}
      />

      <RouteEmptyState
        icon={PackageSearch}
        title="Este pedido todavía no se puede mostrar"
        description="El pedido llega del servicio de la tienda con su estado de compra, su estado de orden y su evidencia de pago. La interfaz no afirma un pago que el proveedor no ha confirmado."
      />

      <RouteEmptyState
        icon={PackageCheck}
        title="La recogida se confirmará en el punto del evento"
        description="Cuando el pedido esté pagado, el personal del punto de control confirmará la recogida allí. El código no se publica en esta pantalla."
      />
    </div>
  );
}
