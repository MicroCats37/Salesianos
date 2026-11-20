"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PasoBannerProps {
  /** The name of the step. */
  titulo: string;
  /** What the visitor has to do in this step. */
  detalle: string;
  /** The icon that names the step. */
  Icono: LucideIcon;
  className?: string;
}

/**
 * PasoBanner - what the step asks for.
 *
 * It is the gesture of the previous frontend: a band of colour that says
 * what is happening NOW and what the visitor has to decide. Without it the
 * wizard is a series of empty boxes and the visitor has to guess.
 *
 * The band is the institutional gradient, not a literal one: the identity of
 * the product is the same everywhere, and the TEXT is what carries the
 * meaning.
 *
 * The band has a hierarchy of three levels: the gold rule that names the
 * brand, the eyebrow that names the step and the lead that names the
 * decision. Below 640 the lead is the size of a body text so the sentence
 * never has to be truncated.
 */
export function PasoBanner({
  titulo,
  detalle,
  Icono,
  className,
}: PasoBannerProps) {
  return (
    <div
      role="note"
      className={cn(
        "relative flex items-start gap-3 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-brand-band p-4 sm:gap-4 sm:p-5",
        className,
      )}
    >
      {/*
       * The rule of the brand along the top edge.
       *
       * It is the same gesture of the section headers of the portada: a
       * two-pixel line of gold that says "this is a band of the festival"
       * without adding a block of colour.
       */}
      <span
        aria-hidden="true"
        className="rule-gold absolute inset-x-0 top-0 h-1"
      />

      <span
        aria-hidden="true"
        className="flex size-11 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-accent text-accent-foreground shadow-[var(--elevation-sm)]"
      >
        <Icono className="size-5" />
      </span>

      <span className="flex min-w-0 flex-col gap-1">
        <span className="text-eyebrow-brand text-primary">{titulo}</span>
        <span className="text-sm leading-relaxed text-foreground sm:text-lead">
          {detalle}
        </span>
      </span>
    </div>
  );
}
