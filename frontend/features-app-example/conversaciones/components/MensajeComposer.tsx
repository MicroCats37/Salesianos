"use client";

import { Paperclip, Send, X } from "lucide-react";
import { useCallback, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import type { Mensaje, UsuarioMencionable } from "../schemas";
import { ChatTextarea } from "./ChatTextarea";

export interface AttachmentWithDescription {
  file: File;
  descripcion: string;
}

/**
 * Subset of UsuarioMencionable fields needed to render a mention display label.
 * Passed from ConversacionPanel → CommentThread so CommentThread can build
 * an internal Map<usuario_id, MentionableUserSummary> without exposing Record<string, …>.
 */
export interface MentionableUserSummary {
  id: string;
  username?: string;
  nombres?: string | null;
  apellidos?: string | null;
  dni?: string | null;
}

/**
 * Legacy alias — retained for backward compatibility with MensajeComposer's
 * internal mention chip rendering (which already has all fields).
 */
export interface MentionItem {
  usuario_id: string;
  username?: string;
  nombres?: string | null;
  apellidos?: string | null;
  dni?: string | null;
}

/**
 * Resolves a mention user object to a display label.
 * Accepts either MentionItem (usuario_id) or MentionableUserSummary (id).
 * Priority: full name → @username → dni → id (fallback).
 */
export function getMentionLabel(
  m: MentionItem | MentionableUserSummary,
): string {
  const id = "usuario_id" in m ? m.usuario_id : m.id;
  const fullName = [m.nombres, m.apellidos]
    .filter((v): v is string => v != null && v.trim() !== "")
    .join(" ")
    .trim();
  if (fullName) return fullName;
  if (m.username) return `@${m.username}`;
  if (m.dni) return m.dni;
  return id;
}

/**
 * Builds a human-readable context label for a mentionable user.
 * Only returns a non-empty string when period context is available
 * (i.e., when area_id is present from a solicitud_id query).
 * Format: "area · rol · ciclo N · Tipo" e.g. "Comercial · Analista · ciclo 1 · Principal"
 */
export function getMentionContextLabel(u: UsuarioMencionable): string {
  const parts: string[] = [];
  if (u.area_nombre) parts.push(u.area_nombre);
  if (u.rol) parts.push(u.rol);
  if (u.numero_ciclo != null) parts.push(`ciclo ${u.numero_ciclo}`);
  if (u.tipo_participacion) {
    // Humanize tipo_participacion for display
    const label =
      u.tipo_participacion === "PRINCIPAL" ? "Principal" : "Adjunta";
    parts.push(label);
  }
  return parts.join(" · ");
}

export interface MensajeComposerProps {
  /** Current message content — controlled value from panel */
  contenido: string;
  /** Current attachments with optional per-file description */
  attachments: AttachmentWithDescription[];
  /** Message being replied to (if any). */
  replyTarget?: Mensaje | null;
  /** Mentioned users for the current message (with optional display data) */
  menciones: MentionItem[];
  /** All mentionable users fetched for this solicitud (passed from ConversacionPanel) */
  usuariosMencionables?: UsuarioMencionable[];
  /** Called when the user types in the textarea */
  onContenidoChange: (value: string) => void;
  /** Called when attachments change (add/remove) */
  onAttachmentsChange: (attachments: AttachmentWithDescription[]) => void;
  /** Called when attachment description changes */
  onAttachmentDescriptionChange: (index: number, descripcion: string) => void;
  /** Called when the user removes a mention */
  onMentionRemove: (usuario_id: string) => void;
  /** Called when a user is selected from the mention dropdown — replaces @query with @username */
  onMentionAdd?: (usuario: UsuarioMencionable) => void;
  /** Called when the user cancels a reply */
  onReplyCancel: () => void;
  /** Called when the user submits a message */
  onSubmit: () => void;
  /** Set to true while a mutation is in-flight */
  isSubmitting?: boolean;
  /** Set to true to disable the composer */
  disabled?: boolean;
  /**
   * Called when the user types @ followed by a search term.
   * Backend dependency: requires a GET /api/usuarios/?search= endpoint.
   * Until that endpoint exists, this callback is a no-op and suggestions
   * will show an empty state.
   */
  onMentionSearch?: (query: string) => void;
}

/**
 * Message composer — presentational/controlled component.
 *
 * Owns NO state. All state (contenido, attachments, replyTarget) is
 * managed by the parent ConversacionPanel.
 *
 * Features:
 * - Auto-growing textarea (80px min, 256px max with scroll)
 * - Ctrl+Enter to submit
 * - Multiple file attachment support
 * - Reply banner with cancel option
 * - @mention trigger detection (backend endpoint pending)
 */
export function MensajeComposer({
  contenido,
  attachments,
  replyTarget,
  menciones,
  usuariosMencionables,
  onContenidoChange,
  onAttachmentsChange,
  onAttachmentDescriptionChange,
  onMentionRemove,
  onReplyCancel,
  onSubmit,
  isSubmitting = false,
  disabled = false,
  onMentionSearch,
  onMentionAdd,
}: MensajeComposerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Track mention query for the suggestions dropdown
  // null = no mention active (dropdown hidden)
  // "" = bare @ active (dropdown shows all options)
  // non-empty = filter query
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);

  // Filtered mentionable users — computed from all usuariosMencionables + local query
  const filteredUsuarios = useMemo(() => {
    if (!usuariosMencionables) return [];
    const query = (mentionQuery ?? "").toLowerCase();
    const selectedIds = new Set(menciones.map((m) => m.usuario_id));
    return usuariosMencionables
      .filter((u) => {
        if (selectedIds.has(u.id)) return false;
        if (!query) return true;
        return (
          (u.nombres ?? "").toLowerCase().includes(query) ||
          (u.apellidos ?? "").toLowerCase().includes(query) ||
          (u.username ?? "").toLowerCase().includes(query) ||
          (u.dni ?? "").toLowerCase().includes(query)
        );
      })
      .slice(0, 7);
  }, [usuariosMencionables, mentionQuery, menciones]);

  /**
   * Replace the trailing @query in contenido with @username and signal the mention.
   */
  const handleMentionSelect = useCallback(
    (usuario: UsuarioMencionable) => {
      // Replace the trailing @<query> with @<username>
      const queryPattern = /@\w*$/;
      const replacement = `@${usuario.username} `;
      const newContenido = contenido.replace(queryPattern, replacement);
      onContenidoChange(newContenido);
      setMentionQuery("");
      onMentionAdd?.(usuario);
    },
    [contenido, onContenidoChange, onMentionAdd],
  );

  const handleChatValueChange = useCallback(
    (value: string) => {
      onContenidoChange(value);
      // Detect @mention search pattern to notify parent
      const match = value.match(/@(\w*)$/);
      if (match) {
        setMentionQuery(match[1]);
        onMentionSearch?.(match[1]);
      } else {
        setMentionQuery(null);
      }
    },
    [onContenidoChange, onMentionSearch],
  );

  const handleSend = useCallback(() => {
    const trimmed = contenido.trim();
    if (!trimmed && attachments.length === 0) return;
    onSubmit();
  }, [contenido, attachments, onSubmit]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) {
      onAttachmentsChange([
        ...attachments,
        ...files.map((file) => ({ file, descripcion: "" })),
      ]);
    }
    // Reset so the same file can be selected again
    e.target.value = "";
  };

  const removeAttachment = (index: number) => {
    onAttachmentsChange(attachments.filter((_, i) => i !== index));
  };

  const isEmpty = !contenido.trim() && attachments.length === 0;

  return (
    <div className="flex flex-col gap-2">
      {/* Reply banner */}
      {replyTarget && (
        <div className="flex items-center gap-2 bg-muted/50 rounded-md px-3 py-2 text-xs">
          <span className="text-muted-foreground shrink-0">
            Respondiendo a:
          </span>
          <span className="flex-1 line-clamp-1 text-muted-foreground">
            {replyTarget.contenido ?? "[mensaje con archivos]"}
          </span>
          <button
            type="button"
            onClick={onReplyCancel}
            className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Cancelar respuesta"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Mention chips */}
      {menciones.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {menciones.map((mencion) => (
            <div
              key={mencion.usuario_id}
              className="flex items-center gap-1 bg-primary/10 text-primary border border-primary/20 rounded px-1.5 py-0.5 text-xs"
            >
              <span>@{getMentionLabel(mencion)}</span>
              <button
                type="button"
                onClick={() => onMentionRemove(mencion.usuario_id)}
                className="text-primary/60 hover:text-primary transition-colors"
                aria-label="Quitar mención"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Attachment previews */}
      {attachments.length > 0 && (
        <div className="flex flex-col gap-2">
          {attachments.map((attachment, index) => (
            <div
              key={`${attachment.file.name}-${attachment.file.size}-${index}`}
              className="flex flex-col gap-1.5 bg-muted/60 border border-border rounded-lg p-2.5"
            >
              <div className="flex items-center gap-2">
                <Paperclip className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                <span className="line-clamp-1 flex-1 text-xs font-medium">
                  {attachment.file.name}
                </span>
                <span className="text-xs text-muted-foreground shrink-0">
                  {(attachment.file.size / 1024).toFixed(1)} KB
                </span>
                <button
                  type="button"
                  onClick={() => removeAttachment(index)}
                  className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
                  aria-label={`Quitar ${attachment.file.name}`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              <input
                type="text"
                placeholder="Descripción (opcional)"
                value={attachment.descripcion}
                onChange={(e) =>
                  onAttachmentDescriptionChange(index, e.target.value)
                }
                className="w-full text-xs bg-background border border-border rounded px-2 py-1 placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2">
        {/* Attachment button */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="shrink-0 h-9 w-9 p-0 self-end mb-0.5"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isSubmitting}
          aria-label="Adjuntar archivos"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Auto-growing textarea + mention suggestions dropdown */}
        <div className="relative flex-1 min-w-0">
          <ChatTextarea
            value={contenido}
            onValueChange={handleChatValueChange}
            placeholder="Escribe un mensaje… (Ctrl+Enter para enviar)"
            disabled={disabled || isSubmitting}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleSend();
              }
            }}
            onMentionSearch={(query) => {
              setMentionQuery(query);
              onMentionSearch?.(query);
            }}
          />
          {/* Mention suggestions dropdown — shown when @query is active */}
          {mentionQuery !== null && (
            <div className="absolute left-0 bottom-full mb-1 z-50 w-72 overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md">
              {filteredUsuarios.length > 0 ? (
                <div className="flex flex-col gap-0.5">
                  {filteredUsuarios.map((usuario) => {
                    const contextLabel = getMentionContextLabel(usuario);
                    return (
                      <button
                        key={usuario.id}
                        type="button"
                        className="flex flex-col items-start gap-0.5 rounded px-2 py-1.5 text-xs hover:bg-accent hover:text-accent-foreground transition-colors w-full text-left"
                        onMouseDown={(e) => {
                          e.preventDefault(); // prevent textarea blur before selection
                          handleMentionSelect(usuario);
                        }}
                      >
                        <span className="font-medium text-foreground">
                          @{usuario.username}
                        </span>
                        <span className="text-muted-foreground">
                          {[usuario.nombres, usuario.apellidos, usuario.dni]
                            .filter(Boolean)
                            .join(" · ")}
                        </span>
                        {contextLabel && (
                          <span className="text-[10px] text-primary/70 italic">
                            {contextLabel}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <p className="px-2 py-1.5 text-xs text-muted-foreground">
                  Sin resultados
                </p>
              )}
            </div>
          )}
        </div>

        {/* Send button */}
        <Button
          type="button"
          size="sm"
          className="shrink-0 h-9 px-3 self-end mb-0.5"
          onClick={handleSend}
          disabled={disabled || isSubmitting || isEmpty}
          aria-label="Enviar mensaje"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      {/* Hint */}
      <p className="text-xs text-muted-foreground">Ctrl+Enter para enviar</p>
    </div>
  );
}
