"use client";

import { Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface SelectorCantidadProps {
  /** The identifier of the field, so the label and the hint can meet it. */
  id: string;
  /** The value the person chose. */
  valor: number;
  /** The change of the value. */
  onChange: (valor: number) => void;
  /**
   * The maximum the adapter knows about.
   *
   * It is OPTIONAL on purpose: the limit of a batch of passes is a rule of
   * the domain (`CANTIDAD_INVALIDA`, 422) and the browser does not enforce
   * it. When the adapter has no maximum, the field is left open and the
   * server decides.
   */
  maximo?: number;
  /** The name of the thing that is counted, in the words of the buyer. */
  sustantivo?: string;
  className?: string;
}

/**
 * SelectorCantidad - the quantity stepper of a batch of passes.
 *
 * It is keyboard operable (the number field is a real number input, the two
 * buttons have an accessible name) and it ANNOUNCES its value in a live
 * region, because a stepper that only changes a number is invisible to a
 * screen reader.
 *
 * The minimum is one: a batch of zero passes is not a batch. The maximum is
 * NOT a client rule (`DOM-03`: the domain declares it and rejects the
 * invalid amount with a stable code).
 */
export function SelectorCantidad({
  id,
  valor,
  onChange,
  maximo,
  sustantivo = "pases",
  className,
}: SelectorCantidadProps) {
  const descriptorId = `${id}-descripcion`;
  const plural = valor === 1 ? sustantivo : `${sustantivo}s`;

  function ajustar(delta: number) {
    const siguiente = valor + delta;

    if (siguiente < 1) return;
    if (maximo !== undefined && siguiente > maximo) return;

    onChange(siguiente);
  }

  return (
    <div className={className}>
      <Label htmlFor={id}>{`Cuántos ${sustantivo} quieres`}</Label>

      <div className="mt-2 flex items-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="min-h-11 min-w-11"
          onClick={() => ajustar(-1)}
          disabled={valor <= 1}
          aria-label="Reducir la cantidad"
        >
          <Minus className="size-4" aria-hidden="true" />
        </Button>

        <Input
          id={id}
          type="number"
          inputMode="numeric"
          min={1}
          max={maximo}
          value={valor}
          onChange={(evento) => {
            const siguiente = Number.parseInt(evento.target.value, 10);

            if (Number.isNaN(siguiente)) return;
            if (siguiente < 1) return;

            onChange(siguiente);
          }}
          aria-describedby={descriptorId}
          className="min-h-11 w-24 text-center tabular-nums"
        />

        <Button
          type="button"
          variant="outline"
          size="icon"
          className="min-h-11 min-w-11"
          onClick={() => ajustar(1)}
          disabled={maximo !== undefined && valor >= maximo}
          aria-label="Aumentar la cantidad"
        >
          <Plus className="size-4" aria-hidden="true" />
        </Button>
      </div>

      <p id={descriptorId} className="mt-2 text-caption text-muted-foreground">
        La cantidad máxima la confirma el servidor al crear la compra.
      </p>

      <p aria-live="polite" className="sr-only">
        {`${valor} ${plural}`}
      </p>
    </div>
  );
}
