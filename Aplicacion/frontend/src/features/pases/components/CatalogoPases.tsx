"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type {
  EnviarCompraPase,
  PaseCatalogo,
  VeredictoPago,
} from "../types/pase.types";
import { DialogoCheckout } from "./DialogoCheckout";
import { ResumenCompra } from "./ResumenCompra";
import { SelectorCantidad } from "./SelectorCantidad";
import { TarjetaPase } from "./TarjetaPase";

export interface CatalogoPasesProps {
  /** The passes of the edition. */
  pases: PaseCatalogo[];
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /** The transport of the purchase. */
  enviar?: EnviarCompraPase;
}

/**
 * CatalogoPases - the composition of the catalogue of passes.
 *
 * It holds the two decisions of the visitor: WHICH pass and HOW MANY. Both
 * are choices, never business rules: the limit of the batch, the price and
 * the availability are decided by the server.
 *
 * The layout follows `RB-02` PASS-01: a single column below 1024 with the
 * call to action at the end, and two columns from 1024 with the summary
 * beside the options. From 1024 the summary STICKS: the buyer chooses the
 * pass and the quantity, and the summary and the call to action stay in
 * sight while the options are being read.
 */
export function CatalogoPases({ pases, pago, enviar }: CatalogoPasesProps) {
  const [seleccionado, setSeleccionado] = useState<PaseCatalogo | null>(null);
  const [cantidad, setCantidad] = useState(1);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start lg:gap-8">
      <section
        aria-labelledby="catalogo-pases-titulo"
        className="flex flex-col gap-4"
      >
        <h2
          id="catalogo-pases-titulo"
          className="text-section-title text-foreground"
        >
          Elige tu pase
        </h2>

        <div
          role="radiogroup"
          aria-label="Pases a la venta"
          className="flex flex-col gap-4"
        >
          {pases.map((pase) => (
            <TarjetaPase
              key={pase.id}
              pase={pase}
              seleccionado={seleccionado?.id === pase.id}
              onSelect={setSeleccionado}
            />
          ))}
        </div>
      </section>

      <section
        aria-labelledby="resumen-pases-titulo"
        className="flex flex-col gap-4 lg:sticky lg:top-20"
      >
        <h2 id="resumen-pases-titulo" className="sr-only">
          Resumen de la compra
        </h2>

        {seleccionado ? (
          <>
            <SelectorCantidad
              id="cantidad-pases"
              valor={cantidad}
              onChange={setCantidad}
            />

            <ResumenCompra pase={seleccionado} cantidad={cantidad} />

            <Button
              type="button"
              className="min-h-11 w-full shadow-[var(--elevation-sm)]"
              onClick={() => setDialogoAbierto(true)}
            >
              Continuar al pago
            </Button>
          </>
        ) : (
          <p className="rounded-[var(--radius-lg)] border border-dashed border-border bg-surface-recessed p-4 text-caption text-muted-foreground">
            Elige un pase para ver el resumen y continuar al pago.
          </p>
        )}
      </section>

      {seleccionado ? (
        <DialogoCheckout
          pase={seleccionado}
          cantidad={cantidad}
          abierto={dialogoAbierto}
          onOpenChange={setDialogoAbierto}
          pago={pago}
          enviar={enviar}
        />
      ) : null}
    </div>
  );
}
