import { cn } from "@/lib/utils";
import type { CuposOperativosOut } from "../types/operaciones.types";

export interface CifrasCuposProps {
  /** The three cupos, as the server publishes them. */
  cupos: CuposOperativosOut;
  className?: string;
}

/**
 * CifrasCupos - the THREE cupos of a record.
 *
 * `GOV-02-RB-04a`: the maximum of a roster and the balance of paid cupos
 * are DIFFERENT numbers and they are never presented as one. This component
 * therefore shows three facts side by side and never a percentage, never a
 * derived balance and never a subtraction: the browser prints the three
 * numbers the server sent.
 */
export function CifrasCupos({ cupos, className }: CifrasCuposProps) {
  const cifras = [
    { etiqueta: "Adquiridos", valor: cupos.adquiridos },
    { etiqueta: "Asignados", valor: cupos.asignados },
    { etiqueta: "Disponibles", valor: cupos.disponibles },
  ];

  return (
    <dl
      data-operacion="cupos"
      className={cn(
        "grid grid-cols-3 gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-recessed/60 p-3",
        className,
      )}
    >
      {cifras.map((cifra) => (
        <div key={cifra.etiqueta} className="flex flex-col gap-0.5">
          <dt className="text-xs text-foreground-muted">{cifra.etiqueta}</dt>
          <dd className="text-lg leading-none font-semibold tabular-nums text-foreground">
            {cifra.valor}
          </dd>
        </div>
      ))}
    </dl>
  );
}
