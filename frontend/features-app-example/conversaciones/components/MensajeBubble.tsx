"use client";

import { Paperclip, Trash2 } from "lucide-react";
import type React from "react";
import { useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { formatDateTime } from "@/utils/date-formatter";
import type { Mensaje, UsuarioMencionable } from "../schemas";
import {
  getMentionContextLabel,
  getMentionLabel,
  type MentionableUserSummary,
} from "./MensajeComposer";

export interface MensajeBubbleProps {
  mensaje: Mensaje;
  /** Current user ID — if provided and matches autor, shows delete button. */
  currentUserId?: string;
  /** Called when the user clicks reply on a message. */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onReply?: (mensaje: Mensaje) => void;
  /** Called when the user requests to delete their own message. */
  onDelete?: (mensajeId: string) => void;
  /** Whether a delete mutation is in-flight for this message. */
  isDeleting?: boolean;
  /** Message being replied to (if any) — used to render reply context. */
  replyingTo?: Mensaje | null;
  /**
   * List of mentionable users for this conversation context.
   * Allows MensajeBubble to render full names for mentions and author
   * instead of raw UUIDs. When fetched with solicitud_id, entries include
   * period context (area_nombre, rol, numero_ciclo, tipo_participacion).
   */
  usuariosMencionables?: UsuarioMencionable[];
}

function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Derives avatar initials from a real name (first + last word). */
function initialsFromName(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

/**
 * Parses message content and replaces @username tokens with inline mention chips.
 * Only replaces tokens whose usuario_id appears in the message's menciones array.
 */
function renderContentWithMentions(
  content: string | null | undefined,
  menciones: { usuario_id: string }[],
  mentionDisplayMap: Map<string, MentionableUserSummary>,
): React.ReactNode[] {
  if (!content) return [];
  const mentionUserIds = new Set(menciones.map((m) => m.usuario_id));
  const tokenRegex = /@(\w+)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null = tokenRegex.exec(content);

  while (match !== null) {
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }

    const username = match[1].toLowerCase();
    let found = false;

    for (const [_id, user] of mentionDisplayMap) {
      if (user.username?.toLowerCase() === username) {
        if (mentionUserIds.has(user.id)) {
          const label = getMentionLabel(user);
          parts.push(
            <span
              key={`mention-${match.index}-${match[0]}`}
              className="inline-flex items-center gap-0.5 text-xs bg-primary/10 text-primary border border-primary/20 rounded px-1 py-0.5 font-medium"
            >
              @{label}
            </span>,
          );
          found = true;
          break;
        }
      }
    }

    if (!found) {
      parts.push(match[0]);
    }

    lastIndex = match.index + match[0].length;
    match = tokenRegex.exec(content);
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [content];
}

/**
 * Renders a single message bubble within a conversation thread.
 * Supports: text content, file attachments, reply context (mensaje_padre_id).
 */
export function MensajeBubble({
  mensaje,
  currentUserId,
  onReply: _onReply,
  onDelete,
  isDeleting = false,
  replyingTo,
  usuariosMencionables,
}: MensajeBubbleProps) {
  const isOwnMessage =
    currentUserId && mensaje.autor_usuario_id
      ? mensaje.autor_usuario_id === currentUserId
      : false;

  const mentionDisplayMap = useMemo(() => {
    if (!usuariosMencionables) return new Map<string, MentionableUserSummary>();
    return new Map<string, MentionableUserSummary>(
      usuariosMencionables.map((u) => [
        u.id,
        {
          id: u.id,
          username: u.username,
          nombres: u.nombres,
          apellidos: u.apellidos,
          dni: u.dni,
        },
      ]),
    );
  }, [usuariosMencionables]);

  // Resolve author display name for prominent showing.
  // Priority: autor_nombre → mentionable full label → username → name-derived initials.
  // For own messages: show real name if available, fall back to "Tú" only
  // when no name data whatsoever exists. Preserves area/role/cycle context.
  const autorData = mentionDisplayMap.get(mensaje.autor_usuario_id ?? "");
  const autorDisplay = !mensaje.autor_usuario_id
    ? "Sistema"
    : (() => {
        // 1. Prefer autor_nombre if available (populated from backend join)
        if (mensaje.autor_nombre) return mensaje.autor_nombre;
        // 2. Fall back to mentionable lookup (works for own and other messages)
        if (autorData) return getMentionLabel(autorData);
        // 3. Fall back to autor_username if available
        if (mensaje.autor_username) return `@${mensaje.autor_username}`;
        // 4. Ultimate fallback — never UUID-derived; only "Tú" when nothing else exists
        return isOwnMessage ? "Tú" : "?";
      })();

  // Avatar initials come from the resolved name — never from a raw UUID slice.
  const initials = (() => {
    if (!mensaje.autor_usuario_id) return "SY";
    const fullName = [autorData?.nombres, autorData?.apellidos]
      .filter((v): v is string => v != null && v.trim() !== "")
      .join(" ")
      .trim();
    if (fullName) return initialsFromName(fullName);
    if (mensaje.autor_nombre) return initialsFromName(mensaje.autor_nombre);
    if (mensaje.autor_username) return initialsFromName(mensaje.autor_username);
    return isOwnMessage ? "TU" : "?";
  })();

  // Resolve author context label (area · rol · ciclo N · Tipo) when available.
  // Shown for all messages including own messages when the user has context data.
  const autorContext = (() => {
    if (!mensaje.autor_usuario_id || !usuariosMencionables) return null;
    const contextUser = usuariosMencionables.find(
      (u) => u.id === mensaje.autor_usuario_id,
    );
    if (!contextUser) return null;
    return getMentionContextLabel(contextUser);
  })();

  const contentWithMentions = useMemo(
    () =>
      renderContentWithMentions(
        mensaje.contenido,
        mensaje.menciones,
        mentionDisplayMap,
      ),
    [mensaje.contenido, mensaje.menciones, mentionDisplayMap],
  );

  return (
    <div className="group flex flex-col gap-1 py-2">
      {/* Reply context banner */}
      {replyingTo && (
        <div
          className={cn(
            "flex items-center gap-2 text-xs text-muted-foreground border-l-2 border-primary/30 mb-1",
            isOwnMessage ? "mr-2 ml-0 justify-end" : "ml-2 mr-0",
          )}
        >
          <span className="font-medium">Respondiendo a:</span>
          <span className="line-clamp-1">
            {replyingTo.contenido ?? "[mensaje con archivos]"}
          </span>
        </div>
      )}

      <div className={cn("flex items-start gap-2")}>
        {/* Avatar */}
        <Avatar
          className={cn(
            "w-8 h-8 border border-border shrink-0",
            isOwnMessage ? "self-start" : "self-start",
          )}
        >
          <AvatarFallback className="text-[10px] font-bold bg-primary/10 text-primary">
            {initials}
          </AvatarFallback>
        </Avatar>

        {/* Content */}
        <div
          className={cn(
            "flex flex-col min-w-0 max-w-[min(38rem,85%)]",
            "items-start",
          )}
        >
          {/* Header: author + context + time, left-aligned */}
          <div className={cn("flex items-center gap-2 mb-0.5", "flex-row")}>
            <span className="text-xs font-medium text-foreground/70">
              {autorDisplay}
            </span>
            {autorContext && (
              <span className="text-xs text-muted-foreground/60 italic">
                {autorContext}
              </span>
            )}
            <span className="text-xs text-muted-foreground">
              {formatDateTime(mensaje.fecha_envio)}
            </span>
            {mensaje.editado_at && (
              <span className="text-xs text-muted-foreground italic">
                (editado)
              </span>
            )}
          </div>

          {/* Message bubble — content + attachments as visual unit, left-aligned */}
          <div
            className={cn(
              "bg-muted/40 rounded-lg border border-border/50 p-2.5 min-w-0 max-w-[min(38rem,85%)]",
              "rounded-tl-none",
            )}
          >
            {/* Text content with inline mention chips */}
            {contentWithMentions.length > 0 && (
              <p
                className="text-sm whitespace-pre-wrap break-words text-foreground/90"
                style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}
              >
                {contentWithMentions}
              </p>
            )}

            {/* Attachments rendered inside bubble as visual extension */}
            {mensaje.archivos_adjuntos.length > 0 && (
              <div className="flex flex-col gap-1 mt-2 pt-2 border-t border-border/30">
                {mensaje.archivos_adjuntos.map((adj) => (
                  <div key={adj.id} className="flex flex-col gap-0.5">
                    <a
                      href={adj.archivo_url ?? "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-xs text-primary hover:underline bg-primary/5 border border-primary/10 rounded px-2 py-1 self-start"
                      download={adj.nombre_original}
                    >
                      <Paperclip className="h-3 w-3 shrink-0" />
                      <span className="line-clamp-1 max-w-[160px]">
                        {adj.nombre_original}
                      </span>
                      {adj.tamano_bytes != null && (
                        <span className="text-muted-foreground shrink-0">
                          ({formatFileSize(adj.tamano_bytes)})
                        </span>
                      )}
                    </a>
                    {adj.descripcion && (
                      <span className="text-[10px] text-muted-foreground italic pl-1">
                        {adj.descripcion}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action buttons — shown on hover for own messages, left-aligned */}
          {isOwnMessage && onDelete && (
            <div
              className={cn(
                "flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity",
                "flex-row",
              )}
            >
              <button
                type="button"
                onClick={() => onDelete(mensaje.id)}
                disabled={isDeleting}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors"
                aria-label="Eliminar mensaje"
              >
                <Trash2 className="h-3 w-3" />
                Eliminar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
