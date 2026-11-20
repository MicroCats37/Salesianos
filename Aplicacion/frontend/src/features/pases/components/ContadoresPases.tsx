import { cn } from "@/lib/utils";
import type { CompraPases } from "../types/pase.types";

export interface ContadoresPasesProps {
  /** The purchase of the batch. */
  compra: CompraPases;
  className?: string;
}

/**
 * ContadoresPases - the three counters of a batch of passes.
 *
 * ADQUIRIDOS, ASIGNADOS and PENDIENTES are three FACTS published by the
 * backend (`cantidad`, `asignados`, `disponibles`). The browser never
 * derives the third one from the first two: it shows the three numbers the
 * server sent, side by side, so a mismatch is visible instead of hidden.
 *
 * A screen reader reads them as a sentence (the values are in the same
 * `<dl>`), because three naked numbers are not a sentence.
 */
export function ContadoresPases({ compra, className }: ContadoresPasesProps) {
  const cifras = [
    { etiqueta: "Adquiridos", valor: compra.cantidad },
    { etiqueta: "Asignados", valor: compra.asignados },
    { etiqueta: "Pendientes", valor: compra.disponibles },
  ];

  return (
    <section
      aria-labelledby="contadores-pases-titulo"
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-4",
        className,
      )}
    >
      <h2 id="contadores-pases-titulo" className="text-section-title text-foreground">
        Tus pases
      </h2>

      <dl className="grid grid-cols-3 gap-3">
        {cifras.map((cifra) => (
          <div key={cifra.etiqueta} className="flex flex-col gap-0.5">
            <dt className="text-caption text-muted-foreground">{cifra.etiqueta}</dt>
            <dd className="text-title-section font-semibold tabular-nums text-foreground">
              {cifra.valor}
            </dd>
          </div>
        ))}
      </dl>

      <p className="text-caption text-muted-foreground">
        {`Has comprado ${compra.cantidad} ${
          compra.cantidad === 1 ? "pase" : "pases"
        }, has asignado ${compra.asignados} y quedan ${compra.disponibles} por asignar.`}
      </p>
    </section>
  );
}
