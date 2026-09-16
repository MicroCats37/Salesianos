"use client";

import { ArrowLeft, MessageSquare, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useConversacionDetail,
  useCrearComentarioSolicitud,
  useCrearMensaje,
  useEliminarMensaje,
  useUsuariosMencionables,
} from "../hooks";
import type { Mensaje } from "../schemas";
import { CommentThread } from "./CommentThread";
import { MensajeComposer } from "./MensajeComposer";

export interface ConversacionPanelProps {
  conversacionId: string | null;
  /** ID of the solicitud — used to fetch mentionable users for this context. */
  solicitudId?: string | null;
  /** ID of the current user — used to show own-message controls. */
  currentUserId?: string;
  /** Set to true to disable the composer (e.g., conversation is closed). */
  disabled?: boolean;
  /** Header context line, e.g. "Solicitud EXP-2026-0142" or "Asesoría Legal · Ciclo 1". */
  contextLabel?: string | null;
  /**
   * Callback to close the conversation panel.
   * Rendered inside the panel header so the control moves with the panel on mobile.
   * Desktop: closes panel, restores full-width main content.
   * Mobile: closes panel, returns to Solicitud view.
   */
  onClose: () => void;
}

/**
 * Chat panel for a single conversation embedded in Solicitud detail.
 *
 * Contract: this panel receives conversacionId from the parent solicitud page.
 * It does NOT create conversations on-demand — old solicitudes without a
 * conversation show a neutral "sin conversación vinculada" state.
 *
 * State ownership:
 * - Composer's contenido, attachments, replyTarget are owned HERE (in panel).
 * - MensajeComposer is purely presentational.
 *
 * Accessibility:
 * - Close/collapse controls are INSIDE this panel header — not in a separate
 *   detached row above the panel. This ensures the control moves with the panel
 *   on mobile (full-width chat view) and stays visually associated.
 * - aria-controls and aria-expanded are managed by the parent page header button.
 */
export function ConversacionPanel({
  conversacionId,
  solicitudId,
  currentUserId,
  disabled = false,
  contextLabel,
  onClose,
}: ConversacionPanelProps) {
  // ── Composer state (owned by panel) ───────────────────────────────────────
  const [contenido, setContenido] = useState("");
  const [attachments, setAttachments] = useState<
    Array<{ file: File; descripcion: string }>
  >([]);
  const [replyTarget, setReplyTarget] = useState<Mensaje | null>(null);
  const [menciones, setMenciones] = useState<
    Array<{
      usuario_id: string;
      username?: string;
      nombres?: string | null;
      apellidos?: string | null;
      dni?: string | null;
    }>
  >([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // ── Queries ───────────────────────────────────────────────────────────────
  const {
    data: conversacion,
    isLoading,
    isError,
  } = useConversacionDetail(conversacionId);

  const { usuarios: usuariosMencionables } = useUsuariosMencionables({
    solicitudId,
  });

  // ── Mutations ──────────────────────────────────────────────────────────────
  /**
   * When solicitudId is present, use the contextual endpoint
   * (POST /solicitudes/{solicitudId}/conversaciones/{conversacionId}/comentarios).
   * Outside a solicitud context (solicId absent), fall back to the generic
   * conversation message endpoint to preserve backward compatibility.
   */
  const crearComentarioSolicitud = useCrearComentarioSolicitud();
  const crearMensaje = useCrearMensaje();
  const eliminarMensaje = useEliminarMensaje();

  // ── Auto-scroll to bottom on new messages ────────────────────────────────
  useEffect(() => {
    if (conversacion?.mensajes?.length) {
      const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      bottomRef.current?.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversacion?.mensajes?.length]);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSubmit = useCallback(() => {
    if (!conversacionId) return;
    const trimmed = contenido.trim();
    if (!trimmed && attachments.length === 0) return;

    const commonVars = {
      conversacionId,
      contenido: trimmed || "",
      archivos: attachments,
      mensaje_padre_id: replyTarget?.id ?? null,
      menciones,
    };

    const onSuccess = () => {
      // Reset composer state after successful send
      setContenido("");
      setAttachments([]);
      setReplyTarget(null);
      setMenciones([]);
    };

    /**
     * Route to contextual endpoint when inside a solicitud.
     * Falls back to generic conversation message endpoint when solicitudId is absent
     * (e.g., if ConversacionPanel is reused outside a solicitud context).
     */
    if (solicitudId) {
      crearComentarioSolicitud.mutate(
        { solicitudId, ...commonVars },
        { onSuccess },
      );
    } else {
      crearMensaje.mutate(commonVars, { onSuccess });
    }
  }, [
    solicitudId,
    conversacionId,
    contenido,
    attachments,
    replyTarget,
    menciones,
    crearComentarioSolicitud,
    crearMensaje,
  ]);

  const handleReply = useCallback((mensaje: Mensaje) => {
    setReplyTarget(mensaje);
  }, []);

  const handleReplyCancel = useCallback(() => {
    setReplyTarget(null);
  }, []);

  const handleMentionRemove = useCallback((usuario_id: string) => {
    setMenciones((prev) => prev.filter((m) => m.usuario_id !== usuario_id));
  }, []);

  const handleMentionAdd = useCallback(
    (usuario: {
      id: string;
      username?: string;
      nombres?: string | null;
      apellidos?: string | null;
      dni?: string | null;
    }) => {
      setMenciones((prev) => {
        if (prev.some((m) => m.usuario_id === usuario.id)) return prev;
        return [
          ...prev,
          {
            usuario_id: usuario.id,
            username: usuario.username,
            nombres: usuario.nombres,
            apellidos: usuario.apellidos,
            dni: usuario.dni,
          },
        ];
      });
    },
    [],
  );

  /**
   * Stub for @mention user search.
   * Backend dependency: requires a GET /api/usuarios/?search=<query> endpoint.
   * Until that endpoint exists, this is a no-op. The MensajeComposer will show
   * a "Sin resultados" suggestion item.
   */
  const handleMentionSearch = useCallback((_query: string) => {
    // TODO: wire to a user-search API when the backend endpoint exists.
    // Expected: GET /api/usuarios/?search=<query> → Array<{ id, nombre, email }>
    // Then update menciones state with the selected user.
  }, []);

  const handleDelete = useCallback(
    (mensajeId: string) => {
      if (!conversacionId) return;
      eliminarMensaje.mutate({ conversacionId, mensajeId });
    },
    [conversacionId, eliminarMensaje],
  );

  const handleAttachmentDescriptionChange = useCallback(
    (index: number, descripcion: string) => {
      setAttachments((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], descripcion };
        return next;
      });
    },
    [],
  );

  // ── Derived state ─────────────────────────────────────────────────────────

  /**
   * isSubmitting reflects the pending state of whichever mutation is active.
   * When inside a solicitud context, the contextual mutation drives the state;
   * outside of it, the generic mutation is used.
   */
  const isSubmitting = solicitudId
    ? crearComentarioSolicitud.isPending
    : crearMensaje.isPending;
  const isClosed = conversacion?.estado === "CERRADA";

  // ── No conversation linked (null id from solicitud detail) ─────────────────
  if (!conversacionId) {
    return (
      <div className="app-card flex flex-col items-center justify-center py-12 text-center gap-3 p-6">
        <MessageSquare className="h-8 w-8 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">
          Sin conversación vinculada a esta solicitud.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="app-card p-4 space-y-3">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (isError || !conversacion) {
    return (
      <div className="app-card flex flex-col items-center justify-center py-12 text-center gap-3 p-6">
        <p className="text-sm text-muted-foreground">
          No se pudo cargar la conversación.
        </p>
      </div>
    );
  }

  return (
    <div className="app-card flex min-h-[30rem] flex-col overflow-hidden p-0 lg:h-[calc(100vh-12rem)] lg:max-h-[44rem]">
      {/* Header — includes inline close/collapse controls so they travel with the panel on mobile */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-muted/30 gap-3">
        {/* Mobile: "Volver a Solicitud" — takes full width on small screens */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="gap-1.5 px-2 lg:hidden"
          aria-label="Volver a la solicitud"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="text-xs">Volver a Solicitud</span>
        </Button>

        {/* Title block — hidden on mobile where the back button takes its place */}
        <div className="hidden lg:flex min-w-0 flex-col gap-0.5 flex-1">
          <div className="flex min-w-0 items-center gap-2">
            <MessageSquare className="h-4 w-4 shrink-0 text-primary" />
            <span className="min-w-0 truncate text-sm font-semibold">
              {conversacion.titulo || "Conversación"}
            </span>
            {isClosed && (
              <span className="inline-flex shrink-0 items-center gap-1 text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60" />
                Cerrada
              </span>
            )}
          </div>
          <span className="truncate pl-6 text-xs text-muted-foreground">
            {conversacion.mensajes?.length ?? 0} mensajes ·{" "}
            {new Date(conversacion.fecha_inicio).toLocaleDateString("es-PE", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
            {contextLabel ? ` · ${contextLabel}` : ""}
          </span>
        </div>

        {/* Desktop: close button — inline in header, right-aligned */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Cerrar conversación"
          className="hidden lg:flex gap-1.5 shrink-0"
        >
          <X className="h-4 w-4" />
          <span className="text-xs">Cerrar</span>
        </Button>
      </div>

      {/* Mobile: title block — shown below the back button on mobile */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/20 lg:hidden">
        <div className="flex min-w-0 flex-col gap-0.5 flex-1 min-w-0">
          <div className="flex min-w-0 items-center gap-2">
            <MessageSquare className="h-4 w-4 shrink-0 text-primary" />
            <span className="min-w-0 truncate text-sm font-semibold">
              {conversacion.titulo || "Conversación"}
            </span>
            {isClosed && (
              <span className="inline-flex shrink-0 items-center gap-1 text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60" />
                Cerrada
              </span>
            )}
          </div>
          <span className="truncate pl-6 text-xs text-muted-foreground">
            {conversacion.mensajes?.length ?? 0} mensajes ·{" "}
            {new Date(conversacion.fecha_inicio).toLocaleDateString("es-PE", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
            {contextLabel ? ` · ${contextLabel}` : ""}
          </span>
        </div>
      </div>

      {/* Scrollable message thread */}
      <ScrollArea className="flex-1 min-h-0 px-4 py-2">
        <CommentThread
          mensajes={conversacion.mensajes ?? []}
          currentUserId={currentUserId}
          onReply={handleReply}
          isDeleting={eliminarMensaje.isPending}
          onDelete={handleDelete}
          usuariosMencionables={usuariosMencionables}
        />
        <div ref={bottomRef} />
      </ScrollArea>

      {/* Sticky composer */}
      <div className="shrink-0 border-t border-border px-4 py-3">
        <MensajeComposer
          contenido={contenido}
          attachments={attachments}
          replyTarget={replyTarget}
          menciones={menciones}
          usuariosMencionables={usuariosMencionables}
          onContenidoChange={setContenido}
          onAttachmentsChange={setAttachments}
          onAttachmentDescriptionChange={handleAttachmentDescriptionChange}
          onMentionRemove={handleMentionRemove}
          onMentionAdd={handleMentionAdd}
          onReplyCancel={handleReplyCancel}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          disabled={disabled || isClosed}
          onMentionSearch={handleMentionSearch}
        />
      </div>
    </div>
  );
}
