import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface AdminCifra {
  /** The stable code of the figure, when the backend publishes one. */
  codigo?: string;
  /** The name of the figure, in the words of the operator. */
  etiqueta: string;
  /** What the figure answers. */
  descripcion?: string;
  /** The value the SERVER calculated. */
  valor: ReactNode;
}

export interface AdminCifrasProps {
  /** The figures published by the backend. */
  cifras: AdminCifra[];
  /** The name of the group of figures, for assistive technology. */
  etiqueta: string;
  className?: string;
}

/**
 * AdminCifras - the figures of a block, read as tiles.
 *
 * A console opens with NUMBERS, and a number inside a row of a table is
 * read one at a time. A tile gives each figure its own surface: the label
 * above, the figure as the dominant element, and the sentence that explains
 * it underneath.
 *
 * The component DERIVES NOTHING: the value it paints is the value the
 * server published. It is a drawing, not a calculation, and it never sums,
 * never compares and never turns a count into a percentage.
 *
 * The figures live in a description list, so the label and its value stay
 * paired for a screen reader and the tile is not a table row pretending to
 * be a card.
 */
export function AdminCifras({ cifras, etiqueta, className }: AdminCifrasProps) {
  if (cifras.length === 0) {
    return null;
  }

  return (
    <dl
      aria-label={etiqueta}
      className={cn(
        "grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4",
        className,
      )}
    >
      {cifras.map((cifra) => (
        <div
          key={cifra.codigo ?? cifra.etiqueta}
          data-cifra
          className="flex flex-col gap-1 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 shadow-[var(--elevation-sm)] transition-shadow duration-(--motion-duration-base) hover:shadow-[var(--elevation-md)]"
        >
          <dt className="text-eyebrow-brand text-muted-foreground">
            {cifra.etiqueta}
          </dt>
          <dd className="flex flex-col gap-1">
            <span className="text-2xl font-bold tracking-tight tabular-nums text-foreground">
              {cifra.valor}
            </span>
            {cifra.descripcion ? (
              <span className="text-xs leading-snug text-muted-foreground">
                {cifra.descripcion}
              </span>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}
