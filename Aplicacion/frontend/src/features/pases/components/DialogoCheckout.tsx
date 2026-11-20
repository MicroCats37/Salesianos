"use client";

import { Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type {
  EnviarCompraPase,
  PaseCatalogo,
  VeredictoPago,
} from "../types/pase.types";
import { EstadoPagoPase } from "./EstadoPagoPase";
import { FormularioComprador } from "./FormularioComprador";

export interface DialogoCheckoutProps {
  /** The pass that is being bought. */
  pase: PaseCatalogo;
  /** The amount of passes. */
  cantidad: number;
  /** Whether the dialog is open. */
  abierto: boolean;
  /** The change of the open state. */
  onOpenChange: (abierto: boolean) => void;
  /**
   * The verdict of the payment, when there already is an order.
   *
   * It is DECLARED by the backend (`estado_operativo`). The dialog never
   * derives a payment state from the fact that the window was closed
   * (`GOV-02-RB-02d`).
   */
  pago?: VeredictoPago;
  /**
   * The transport of the purchase.
   *
   * The purchase is registered by the server and the batch stays PENDING:
   * the dialog never says that a payment was confirmed.
   */
  enviar?: EnviarCompraPase;
}

/**
 * DialogoCheckout - the checkout of a batch of passes.
 *
 * It is the checkout of the PASS module, and only of it: there is no mixed
 * cart between registrations, passes and store products
 * (`GOV-02-RB-02a`).
 *
 * **Closing the window never deletes the purchase** (`QA-C01`,
 * `GOV-02-RB-02b`). The dialog says it, and the button that closes it is
 * named "Cerrar" and not "Cancelar la compra": closing is not cancelling and
 * it is not a confirmed payment either.
 */
export function DialogoCheckout({
  pase,
  cantidad,
  abierto,
  onOpenChange,
  pago,
  enviar,
}: DialogoCheckoutProps) {
  return (
    <Dialog open={abierto} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Datos del comprador</DialogTitle>
          <DialogDescription>
            {`Compras ${cantidad} ${cantidad === 1 ? "pase" : "pases"} de ${pase.nombre}. El comprador puede ser una persona distinta de quienes asisten a la fiesta.`}
          </DialogDescription>
        </DialogHeader>

        {pago ? (
          <div className="rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-4">
            <EstadoPagoPase veredicto={pago} conDescripcion />
          </div>
        ) : null}

        <FormularioComprador enviar={enviar} pase={pase} cantidad={cantidad} />

        <p className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3 text-caption text-muted-foreground">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            Si cierras esta ventana, la compra no se borra: la retomas con el
            enlace de gestión. Cerrar no cancela la compra ni confirma el pago.
          </span>
        </p>

        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline" className="min-h-11">
              Cerrar
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
