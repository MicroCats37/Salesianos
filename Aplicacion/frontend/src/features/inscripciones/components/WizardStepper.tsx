"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * One step of the wizard.
 *
 * The four steps are the ones the flow declares (frontend/02 SPORT-01):
 * the package, the teams, the summary of what the server will do and the
 * confirmation.
 */
export interface WizardPaso {
  id: number;
  titulo: string;
  detalle: string;
}

export interface WizardStepperProps {
  pasos: readonly WizardPaso[];
  /** The step the visitor is on. */
  actual: number;
  className?: string;
}

/**
 * WizardStepper - where the visitor is in the wizard.
 *
 * It is an ORDERED LIST, not a row of decorations: the steps are the
 * structure of the form and the assistive technology has to read them in
 * order. The current step is marked with `aria-current="step"`, the completed
 * ones carry a check, and the pending ones carry their number.
 *
 * The rail NEVER scrolls horizontally: at 360 the four nodes fit in one row
 * and the title of the current step is written above it. From 768 every step
 * shows its own title and its detail.
 *
 * The marker is never the colour alone: the shape of the icon, the number
 * and the wording say the same thing.
 */
export function WizardStepper(props: WizardStepperProps) {
  const { pasos, actual, className } = props;

  const pasoActual = pasos.find((paso) => paso.id === actual) ?? pasos[0];

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <p className="flex flex-wrap items-baseline gap-x-2 sm:hidden">
        <span className="text-caption text-muted-foreground">
          Paso {actual} de {pasos.length}
        </span>
        <span className="text-sm font-semibold text-foreground">
          {pasoActual?.titulo}
        </span>
      </p>

      <ol className="grid grid-cols-4 gap-2">
        {pasos.map((paso, indice) => {
          const activo = actual === paso.id;
          const completado = actual > paso.id;
          const ultimo = indice === pasos.length - 1;

          return (
            <li
              key={paso.id}
              aria-current={activo ? "step" : undefined}
              className="flex min-w-0 flex-col gap-2"
            >
              <span className="flex items-center gap-2">
                <span
                  className={cn(
                    "flex size-9 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold",
                    activo &&
                      "border-accent bg-accent text-accent-foreground shadow-[var(--elevation-sm)]",
                    completado &&
                      "border-success bg-success/15 text-success",
                    !activo &&
                      !completado &&
                      "border-border bg-muted text-muted-foreground",
                  )}
                >
                  {completado ? (
                    <Check className="size-4" aria-hidden="true" />
                  ) : (
                    paso.id
                  )}
                </span>

                {!ultimo ? (
                  <span
                    aria-hidden="true"
                    className={cn(
                      "hidden h-0.5 flex-1 rounded-full sm:block",
                      completado ? "bg-success/40" : "bg-border",
                    )}
                  />
                ) : null}
              </span>

              <span
                className={cn(
                  "hidden text-sm font-semibold leading-tight sm:block",
                  activo
                    ? "text-foreground"
                    : completado
                      ? "text-success"
                      : "text-muted-foreground",
                )}
              >
                {paso.titulo}
              </span>

              <span className="hidden text-caption leading-snug text-muted-foreground lg:block">
                {paso.detalle}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
