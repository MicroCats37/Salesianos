"use client";

import { RefreshCw, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface CompetenciaErrorAlertProps {
  /** The failure of the command, as the mutation hook exposes it. */
  error: { message: string; status?: number };
  /** Send the command again. */
  onReintentar?: () => void;
  /** Label of the retry button. */
  reintentarLabel?: string;
}

/**
 * CompetenciaErrorAlert — the failure of a command of the module.
 *
 * The failure is rendered as an ALERT (the role that the assistive
 * technologies announce) and it is never a dead end: a conflict (409
 * `RESOURCE_CHANGED`) explains that the data was refreshed and offers the
 * retry.
 */
export function CompetenciaErrorAlert({
  error,
  onReintentar,
  reintentarLabel = "Reintentar",
}: CompetenciaErrorAlertProps) {
  const conflicto = error.status === 409;

  return (
    <div
      role="alert"
      className="space-y-2 rounded-xl border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive"
    >
      <p className="flex items-start gap-2 font-medium">
        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{error.message}</span>
      </p>

      {conflicto ? (
        <p className="pl-6">
          Otro administrador cambió este recurso. Los datos se recargaron:
          revisa los valores y vuelve a intentarlo.
        </p>
      ) : null}

      {onReintentar ? (
        <div className="pl-6">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onReintentar}
          >
            <RefreshCw className="mr-2 h-3.5 w-3.5" aria-hidden="true" />
            {reintentarLabel}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
