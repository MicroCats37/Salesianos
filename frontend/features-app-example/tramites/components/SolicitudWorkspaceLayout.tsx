/**
 * SolicitudWorkspaceLayout — main content + integrated collapsible conversation panel.
 *
 * Non-modal layout contract (operational report):
 * - Chat closed: main content uses the full available width.
 * - Chat open (desktop): integrated side panel ~45-50%, main content reflows
 *   to the other half via flex classes. No overlay, backdrop, blur or Sheet.
 * - Chat open (mobile): non-modal navigable view — main content is hidden and
 *   the conversation renders full width; "Volver a Solicitud" restores it.
 *
 * Chat open/close controls are INSIDE the ConversacionPanel header — not in
 * a detached row above the panel.
 */
"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export const SOLICITUD_CONVERSACION_PANEL_ID = "solicitud-conversacion-panel";

export interface SolicitudWorkspaceLayoutProps {
  /** Whether the conversation panel is open (integrated side panel, not modal). */
  chatOpen: boolean;
  /**
   * Callback to close the conversation and restore full-width content.
   * Passed to the chat panel so close controls live inside the panel header.
   */
  onCloseChat: () => void;
  /**
   * Conversation panel content. Receives onCloseChat via render-prop pattern
   * so the close/collapse control lives inside the panel header.
   */
  chatPanel: (props: { onClose: () => void }) => ReactNode;
  /** Main operational content (executive summary, flow, detail sections). */
  children: ReactNode;
}

export function SolicitudWorkspaceLayout({
  chatOpen,
  onCloseChat,
  chatPanel,
  children,
}: SolicitudWorkspaceLayoutProps) {
  return (
    <div className="flex min-w-0 flex-col gap-6 lg:flex-row lg:items-start">
      {/* Main content column — full width when closed, reflows to ~55% when open */}
      <div
        className={cn(
          "min-w-0 space-y-6 lg:flex-1",
          chatOpen && "hidden lg:block",
        )}
      >
        {children}
      </div>

      {chatOpen && (
        <aside
          id={SOLICITUD_CONVERSACION_PANEL_ID}
          aria-label="Conversación"
          className="flex w-full min-w-0 flex-col gap-3 lg:sticky lg:top-6 lg:w-[45%] lg:max-w-[50%] lg:flex-none"
        >
          {chatPanel({ onClose: onCloseChat })}
        </aside>
      )}
    </div>
  );
}
