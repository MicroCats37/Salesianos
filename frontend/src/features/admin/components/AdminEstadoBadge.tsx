"use client";

import { cn } from "@/lib/utils";
import type { AdminTone } from "../utils/admin.estado.utils";
import { toneClasses } from "../utils/admin.tone";

export interface AdminEstadoBadgeProps {
  /** Text of the badge. */
  etiqueta: string;
  /** Visual tone of the state. */
  tono: AdminTone;
  className?: string;
}

/**
 * AdminEstadoBadge — the badge of every operational state.
 *
 * The badge NEVER decides what a state means: it receives the label and the
 * tone that the mappers of `utils/admin.estado.utils.ts` derived from the
 * vocabulary of the backend.
 */
export function AdminEstadoBadge({
  etiqueta,
  tono,
  className,
}: AdminEstadoBadgeProps) {
  const clases = toneClasses(tono);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-wider",
        clases.soft,
        clases.border,
        clases.value,
        className,
      )}
    >
      {etiqueta}
    </span>
  );
}
