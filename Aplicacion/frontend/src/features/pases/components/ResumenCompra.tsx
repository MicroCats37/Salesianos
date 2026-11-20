import { cn } from "@/lib/utils";
import type { PaseCatalogo } from "../types/pase.types";
import { formatearMonto } from "../utils/monto";

export interface ResumenCompraProps {
  /** The chosen pass of the catalogue. */
  pase: PaseCatalogo;
  /** The amount of passes the person chose. */
  cantidad: number;
  className?: string;
}

/**
 * ResumenCompra - what the person is about to buy.
 *
 * The summary shows the price of the CATALOGUE, the chosen quantity and the
 * pass. It does NOT show a total: the total is resolved by the server against
 * the current catalogue (`RN-C02`) and the browser never computes a price
 * (`frontend/03` PASS-01, "el precio lo fija el servidor").
 */
export function ResumenCompra({ pase, cantidad, className }: ResumenCompraProps) {
  return (
    <section
      aria-labelledby="resumen-compra-titulo"
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4",
        className,
      )}
    >
      <h3 id="resumen-compra-titulo" className="text-section-title text-foreground">
        Tu compra
      </h3>

      <dl className="grid gap-3 sm:grid-cols-3">
        <div className="flex flex-col gap-0.5">
          <dt className="text-caption text-muted-foreground">Pase</dt>
          <dd className="text-sm font-semibold text-foreground">{pase.nombre}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-caption text-muted-foreground">Cantidad</dt>
          <dd className="text-sm font-semibold tabular-nums text-foreground">
            {cantidad}
          </dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="text-caption text-muted-foreground">
            Precio unitario
          </dt>
          <dd className="text-sm font-semibold tabular-nums text-foreground">
            {formatearMonto(pase.precio.monto, pase.precio.moneda)}
          </dd>
        </div>
      </dl>

      <p className="text-caption text-muted-foreground">
        El total lo confirma el servidor al crear la compra, con el precio
        vigente en ese momento.
      </p>
    </section>
  );
}
