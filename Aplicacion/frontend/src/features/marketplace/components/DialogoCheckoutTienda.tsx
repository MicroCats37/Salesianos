"use client";

import { TriangleAlert } from "lucide-react";
import { useState } from "react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { ProductoDetalle, VeredictoPago } from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";
import { EstadoPagoTienda } from "./EstadoPagoTienda";

export interface DialogoCheckoutTiendaProps {
  /** The product that is being bought. */
  producto: ProductoDetalle;
  /** The amount of units. */
  cantidad: number;
  /** Whether the dialog is open. */
  abierto: boolean;
  /** The change of the open state. */
  onOpenChange: (abierto: boolean) => void;
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /** The currency of the price, when the edition publishes one. */
  moneda?: string;
  /**
   * The creation of the order.
   *
   * It is NOT wired: `PedidoController` is not registered in the backend, so
   * `POST /marketplace/pedidos` does not exist (`A0-RTV-02`). The seam stays
   * so the binding is one line the day the route is registered; until then
   * the dialog says that no order was created and it never fabricates one.
   */
  crearPedido?: () => Promise<void>;
}

/**
 * DialogoCheckoutTienda - the checkout of the store.
 *
 * It is the checkout of the STORE, and only of it: there is no mixed cart
 * between registrations, passes and store products (`GOV-02-RB-02a`).
 *
 * The dialog does NOT collect the identity of the buyer: the payload of the
 * order (`CrearPedidoIn`) declares only the items, so asking for a document
 * here would be inventing a field the backend does not accept.
 *
 * **Closing the window never deletes the order** (`QA-C01`). The button is
 * named "Cerrar" and not "Cancelar el pedido".
 */
export function DialogoCheckoutTienda({
  producto,
  cantidad,
  abierto,
  onOpenChange,
  pago,
  moneda,
  crearPedido,
}: DialogoCheckoutTiendaProps) {
  const [fase, setFase] = useState<"inicial" | "enviando" | "sin-servicio">(
    "inicial",
  );

  async function alContinuar() {
    if (!crearPedido) {
      setFase("sin-servicio");
      return;
    }

    setFase("enviando");
    await crearPedido();
    setFase("inicial");
  }

  return (
    <Dialog open={abierto} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Tu pedido</DialogTitle>
          <DialogDescription>
            {`${cantidad} ${cantidad === 1 ? "unidad" : "unidades"} de ${producto.nombre}. El total lo confirma el servidor al crear el pedido, con el precio vigente en ese momento.`}
          </DialogDescription>
        </DialogHeader>

        {pago ? (
          <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
            <EstadoPagoTienda veredicto={pago} conDescripcion />
          </div>
        ) : null}

        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-0.5">
            <dt className="text-caption text-muted-foreground">Producto</dt>
            <dd className="text-sm font-semibold text-foreground">
              {producto.nombre}
            </dd>
          </div>
          <div className="flex flex-col gap-0.5">
            <dt className="text-caption text-muted-foreground">
              Precio unitario
            </dt>
            <dd className="text-sm font-semibold tabular-nums text-foreground">
              {formatearMonto(producto.precio_efectivo, moneda ?? "")}
            </dd>
          </div>
        </dl>

        <p className="text-caption text-muted-foreground">
          Si cierras esta ventana, el pedido no se borra: lo retomas con el
          enlace de seguimiento. Cerrar no cancela el pedido ni confirma el
          pago.
        </p>

        {fase === "sin-servicio" ? (
          <Alert>
            <TriangleAlert className="size-4" aria-hidden="true" />
            <AlertTitle>El pedido todavía no está disponible</AlertTitle>
            <AlertDescription>
              El servicio de pedidos de la tienda todavía no está publicado,
              así que no se ha creado ningún pedido. Vuelve a intentarlo en
              unos segundos.
            </AlertDescription>
          </Alert>
        ) : null}

        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline" className="min-h-11">
              Cerrar
            </Button>
          </DialogClose>
          <Button
            type="button"
            className="min-h-11"
            disabled={fase === "enviando"}
            onClick={() => {
              void alContinuar();
            }}
          >
            {fase === "enviando" ? "Creando el pedido" : "Continuar al pago"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
