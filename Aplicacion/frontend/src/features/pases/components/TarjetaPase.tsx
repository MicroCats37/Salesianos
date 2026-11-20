import { Ticket } from "lucide-react";
import { Badge } from "@/components/ui/badge";
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
 * The card reads like a TICKET and not like a generic card: the medallion
 * gives it an identity, the NAME says what it is, the EDITION is the badge
 * that qualifies it and the PRICE is the dominant figure — it is the number
 * the buyer came for.
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
        "group flex min-h-11 w-full flex-col items-start gap-4 rounded-[var(--radius-xl)] border p-5 text-left transition-colors duration-(--motion-duration-fast)",
        seleccionado
          ? "cursor-pointer border-primary bg-primary/5 shadow-[var(--elevation-md)] ring-2 ring-primary/20"
          : bloqueado
            ? "cursor-not-allowed border-destructive/40 bg-destructive/5 opacity-80"
            : "cursor-pointer border-border bg-surface-raised hover:border-border-strong",
        className,
      )}
    >
      <span className="flex w-full items-start justify-between gap-3">
        <span className="flex min-w-0 items-center gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-primary/10 text-primary">
            <Ticket className="size-5" aria-hidden="true" />
          </span>

          <span className="text-base font-bold text-foreground">
            {pase.nombre}
          </span>
        </span>

        <Badge
          variant="outline"
          className="max-w-[50%] border-border bg-surface-recessed text-foreground-muted"
        >
          {pase.edicion_nombre}
        </Badge>
      </span>

      <span className="flex flex-col gap-0.5">
        <span className="text-2xl font-bold tabular-nums text-foreground">
          {formatearMonto(pase.precio.monto, pase.precio.moneda)}
        </span>
        <span className="text-caption text-muted-foreground">por pase</span>
      </span>

      {pase.descripcion ? (
        <span className="text-sm leading-relaxed text-muted-foreground">
          {pase.descripcion}
        </span>
      ) : null}

      {bloqueado ? (
        <span className="text-caption font-semibold text-destructive">
          {motivoBloqueo}
        </span>
      ) : null}
    </button>
  );
}
