"use client";

import type { LucideIcon } from "lucide-react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * One step of the wizard.
 *
 * The five steps are the ones the flow declares (frontend/02 SPORT-01):
 * the package and the people, the cohort, the teams, the summary of what the
 * server will do and the confirmation.
 */
export interface WizardPaso {
  id: number;
  titulo: string;
  detalle: string;
  /** The icon that names the step. */
  Icono?: LucideIcon;
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
 * ones carry a check, and the pending ones carry their icon.
 *
 * The rail NEVER scrolls horizontally: at 360 the title of the current step is
 * written above it and the nodes keep their size. From 640 every step shows
 * its own title next to its node, exactly as the previous frontend had it.
 *
 * The marker is never the colour alone: the shape of the icon, the number
 * and the wording say the same thing.
 */
export function WizardStepper(props: WizardStepperProps) {
  const { pasos, actual, className } = props;

  const pasoActual = pasos.find((paso) => paso.id === actual) ?? pasos[0];

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border bg-surface-recessed p-3 sm:p-4",
        className,
      )}
    >
      {/*
       * The caption of the narrow viewport.
       *
       * At 360 the rail of five nodes does not fit next to their titles, so
       * the title of the CURRENT step is written above it. The eyebrow says
       * the position and the title says the decision: the visitor never has
       * to guess where he/she is.
       */}
      <p className="flex flex-wrap items-baseline gap-x-2 sm:hidden">
        <span className="text-eyebrow-brand text-primary">
          Paso {actual} de {pasos.length}
        </span>
        <span className="text-section-title text-foreground">
          {pasoActual?.titulo}
        </span>
      </p>

      <ol
        aria-label="Pasos de la inscripción"
        className="flex items-center gap-2 sm:gap-3"
      >
        {pasos.map((paso, indice) => {
          const activo = actual === paso.id;
          const completado = actual > paso.id;
          const ultimo = indice === pasos.length - 1;
          const Icono = paso.Icono;

          return (
            <li
              key={paso.id}
              aria-current={activo ? "step" : undefined}
              className={cn(
                "flex min-w-0 items-center gap-2",
                !ultimo && "flex-1",
              )}
            >
              {/*
               * The node of the step.
               *
               * The SHAPE carries the state and never the colour alone: a
               * check for a completed step, the icon of the step for the
               * current one and the NUMBER for a pending step. The node is
               * decorative for the assistive technology (the position is
               * announced in words below), so it is hidden from it.
               */}
              <span
                aria-hidden="true"
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors duration-(--motion-duration-fast)",
                  activo &&
                    "border-accent bg-accent text-accent-foreground shadow-[var(--elevation-sm)] ring-4 ring-accent/20",
                  completado && "border-success bg-success/15 text-success",
                  !activo &&
                    !completado &&
                    "border-border bg-muted text-muted-foreground",
                )}
              >
                {completado ? (
                  <Check className="size-4" />
                ) : Icono ? (
                  <Icono className="size-4" />
                ) : (
                  paso.id
                )}
              </span>

              {/*
               * The name of the step.
               *
               * It is always in the accessibility tree (`sr-only` below 640,
               * visible from 640) and it always carries the POSITION in
               * words, so the rail never depends on the colour to say where
               * the visitor is.
               */}
              <span
                className={cn(
                  "sr-only truncate text-sm font-semibold leading-tight sm:not-sr-only",
                  activo
                    ? "text-foreground"
                    : completado
                      ? "text-success"
                      : "text-muted-foreground",
                )}
              >
                <span className="sr-only">
                  {`Paso ${paso.id} de ${pasos.length}: `}
                </span>
                {paso.titulo}
              </span>

              {/*
               * The rule that joins two steps.
               *
               * It is filled when the step on its left is already done, and
               * it is the gold rule of the brand when it is the segment that
               * LEADS INTO the current step: the eye reads the progress
               * without counting the nodes.
               */}
              {!ultimo ? (
                <span
                  aria-hidden="true"
                  className={cn(
                    "hidden h-0.5 flex-1 rounded-full transition-colors duration-(--motion-duration-base) sm:block",
                    completado
                      ? indice + 1 === actual
                        ? "rule-gold"
                        : "bg-success/40"
                      : "bg-border",
                  )}
                />
              ) : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
