import { Ticket } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PaseCatalogo } from "../types/pase.types";
import { formatearMonto } from "../utils/monto";

export interface TarjetaPaseProps {
  /** The pass of the catalogue. */
  pase: PaseCatalogo;
  /** Whether this pass is the chosen one. */
  seleccionado?: boolean;
  /** The selection. */
  onSelect?: (pase: PaseCatalogo) => void;
  /**
   * Whether the pass cannot be bought.
   *
   * The reason is written by the person: a disabled control without a reason
   * is a dead end (`SH-03` §1, S-02).
   */
  motivoBloqueo?: string;
  className?: string;
}

/**
 * TarjetaPase - one option of the catalogue of passes.
 *
 * The card is a BUTTON: the whole card is the target of the selection, and
 * `aria-pressed` says which one is chosen. The price is the one the backend
 * published for the current edition; the browser never computes it.
 *
 * The pass is NOT a branch of the sports registration: it says so in its own
 * copy, because a visitor who arrives here has to understand in one sentence
 * what they are buying.
 */
export function TarjetaPase({
  pase,
  seleccionado = false,
  onSelect,
  motivoBloqueo,
  className,
}: TarjetaPaseProps) {
  const bloqueado = Boolean(motivoBloqueo);

  return (
    <button
      type="button"
      aria-pressed={seleccionado}
      disabled={bloqueado || !onSelect}
      onClick={() => onSelect?.(pase)}
      className={cn(
        "flex w-full flex-col items-start gap-3 rounded-[var(--radius-lg)] border bg-surface-raised p-4 text-left transition-colors duration-(--motion-duration-base)",
        seleccionado
          ? "border-primary ring-2 ring-primary/25"
          : "border-border",
        bloqueado
          ? "cursor-not-allowed opacity-70"
          : "hover:border-border-strong",
        className,
      )}
    >
      <span className="flex w-full items-start justify-between gap-3">
        <span className="flex flex-col gap-1">
          <span className="text-base font-semibold text-foreground">
            {pase.nombre}
          </span>
          <span className="text-caption text-muted-foreground">
            {pase.edicion_nombre}
          </span>
        </span>

        <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-surface-recessed px-2.5 py-1">
          <Ticket className="size-3.5 text-muted-foreground" aria-hidden="true" />
          <span className="text-xs font-semibold text-foreground">
            {formatearMonto(pase.precio.monto, pase.precio.moneda)}
          </span>
        </span>
      </span>

      {pase.descripcion ? (
        <span className="text-sm text-muted-foreground">{pase.descripcion}</span>
      ) : null}

      {bloqueado ? (
        <span className="text-caption font-semibold text-destructive">
          {motivoBloqueo}
        </span>
      ) : null}
    </button>
  );
}
