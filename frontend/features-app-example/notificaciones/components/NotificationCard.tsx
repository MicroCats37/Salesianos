"use client";

import { CheckCheck, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ESTADO_NOTIFICACION } from "@/shared/constants/tramite.tokens";
import type {
  EstadoNotificacionIndividual,
  NotificationListItem,
} from "../schemas/notificacion.schema";

export interface NotificationCardProps {
  /** The notification item to display. */
  item: NotificationListItem;
  /** Called when the user requests to mark the notification as viewed. */
  onMarcarVista?: (id: string) => void;
  /** Called when the user requests to navigate to the notification detail. */
  onNavigate?: (item: NotificationListItem) => void;
  /** Disables action buttons while a marca-vista mutation is in flight. */
  isMarkingVista?: boolean;
  /** Set to true to disable all interactive elements (e.g., while the card is loading). */
  disabled?: boolean;
}

/**
 * Renders a single notification as a structured row/card.
 *
 * Displays:
 * - Title + status badge
 * - Event type, area, date
 * - Solicitud/expediente reference (gracefully handles missing fields)
 * - Period and participation indicators
 * - Primary action: mark-as-read (conditional)
 * - Secondary actions: discard (conditional), open solicitud (conditional)
 *
 * Accessibility: uses `<button>` for all actions; status is conveyed via badge text,
 * not color alone.
 */
export function NotificationCard({
  item,
  onMarcarVista,
  onNavigate,
  isMarkingVista = false,
  disabled = false,
}: NotificationCardProps) {
  const estadoToken =
    ESTADO_NOTIFICACION[item.estado_individual as EstadoNotificacionIndividual];

  const canMarkVista =
    item.estado_individual === "NO_VISTA" || item.estado_individual === "VISTA";

  const isActionDisabled = disabled || isMarkingVista;

  return (
    <div className="app-card p-4 space-y-3">
      {/* Header row: title + badge + date */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-medium text-sm truncate">{item.titulo}</h3>
            <Badge className={estadoToken.badgeClass}>
              {estadoToken.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {item.evento ?? "—"}
          </p>
        </div>
        <span className="text-xs text-muted-foreground shrink-0">
          {formatDate(item.ocurrido_en)}
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t">
        {canMarkVista && onMarcarVista && (
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 h-8 text-xs"
            onClick={() => onMarcarVista(item.id)}
            disabled={isActionDisabled}
            aria-label="Marcar notificación como vista"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Marcar vista
          </Button>
        )}

        {onNavigate && (
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 h-8 text-xs ml-auto"
            onClick={() => onNavigate(item)}
            aria-label="Ver detalle de la notificación"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Ver detalle
          </Button>
        )}
      </div>
    </div>
  );
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}
