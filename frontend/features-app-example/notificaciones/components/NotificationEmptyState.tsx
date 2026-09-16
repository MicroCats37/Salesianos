import { BellOff } from "lucide-react";
import type { NotificationFilterTab } from "./NotificationTabs";

export interface NotificationEmptyStateProps {
  /**
   * The currently active filter tab.
   * Used to render an appropriate empty message per filter context.
   */
  activeFilter?: NotificationFilterTab;
}

/**
 * Empty state shown when the notifications list returns no items.
 * Adapts copy based on which filter tab is active.
 */
export function NotificationEmptyState({
  activeFilter = "TODAS",
}: NotificationEmptyStateProps) {
  const { title, description } = getEmptyContent(activeFilter);

  return (
    <div className="app-card flex flex-col items-center justify-center py-16 gap-4 text-center">
      <div className="p-4 bg-muted rounded-full">
        <BellOff className="h-8 w-8 text-muted-foreground" />
      </div>
      <div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

function getEmptyContent(filter: NotificationFilterTab): {
  title: string;
  description: string;
} {
  switch (filter) {
    case "NO_VISTA":
      return {
        title: "Sin notificaciones sin leer",
        description: "No tienes notificaciones sin abrir. ¡Todo está al día!",
      };
    case "ABIERTA":
      return {
        title: "Sin notificaciones abiertas",
        description: "No hay notificaciones abiertas.",
      };
    case "PENDIENTE":
      return {
        title: "Sin notificaciones pendientes",
        description: "No tienes notificaciones pendientes de revisar.",
      };
    case "TODAS":
    default:
      return {
        title: "Sin notificaciones",
        description: "No tienes notificaciones pendientes",
      };
  }
}
