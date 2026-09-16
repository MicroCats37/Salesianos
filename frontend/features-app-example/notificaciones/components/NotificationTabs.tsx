"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { EstadoNotificacionIndividual } from "../schemas/notificacion.schema";

export type NotificationFilterTab =
  | "TODAS"
  | "NO_VISTA"
  | "ABIERTA"
  | "PENDIENTE";

export interface NotificationTabsProps {
  /** Currently selected filter tab value. */
  value: NotificationFilterTab;
  /** Called when the user selects a different tab. */
  onChange: (tab: NotificationFilterTab) => void;
  /** Optional per-tab item counts (excluding "TODAS" which is derived). */
  counts?: Partial<Record<EstadoNotificacionIndividual, number>>;
}

/**
 * Filter tabs for the notifications list.
 * Tabs: Todas, Sin abrir (NO_VISTA), Abiertas (ABIERTA), Pendientes.
 * "Archivadas" (DESCARTADA) is intentionally excluded for MVP scope.
 */
export function NotificationTabs({
  value,
  onChange,
  counts,
}: NotificationTabsProps) {
  return (
    <Tabs
      value={value}
      onValueChange={(v) => onChange(v as NotificationFilterTab)}
    >
      <TabsList variant="default">
        <TabsTrigger value="TODAS">Todas</TabsTrigger>

        <TabsTrigger value="NO_VISTA">
          Sin abrir
          {counts?.NO_VISTA != null && counts.NO_VISTA > 0 && (
            <span className="ml-1.5 rounded-md bg-destructive/10 px-1.5 py-0.5 text-[10px] font-semibold text-destructive">
              {counts.NO_VISTA}
            </span>
          )}
        </TabsTrigger>

        <TabsTrigger value="ABIERTA">
          Abiertas
          {counts?.ABIERTA != null && counts.ABIERTA > 0 && (
            <span className="ml-1.5 rounded-md bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600">
              {counts.ABIERTA}
            </span>
          )}
        </TabsTrigger>

        <TabsTrigger value="PENDIENTE">
          Pendientes
          {counts?.VISTA != null && counts.VISTA > 0 && (
            <span className="ml-1.5 rounded-md bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-amber-600">
              {counts.VISTA}
            </span>
          )}
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
