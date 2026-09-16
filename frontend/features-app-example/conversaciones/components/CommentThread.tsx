/**
 * CommentThread — threaded message view for conversation detail.
 *
 * Builds a tree from flat mensajes using mensaje_padre_id.
 * Renders root messages (level 0) with nested replies (level 1+).
 * Uses shadcn Message components for proper chat bubble styling.
 *
 * Frontend depth is capped at MAX_VISIBLE_DEPTH levels.
 * Replies beyond that level are not rendered, and the reply button
 * only appears on messages below MAX_VISIBLE_DEPTH.
 */
import { Paperclip, Reply } from "lucide-react";
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

const MAX_VISIBLE_DEPTH = 3; // 0 = root, 1+ = replies

// ── Types ───────────────────────────────────────────────────────────────────────

interface MensajeTree extends Mensaje {
  children: MensajeTree[];
}

// ── Helpers ────────────────────────────────────────────────────────────────────

/** Derives avatar initials from a real name (first + last word). */
function initialsFromName(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

/**
 * Parses message content and replaces @username tokens with inline mention chips.
 * Only replaces tokens whose usuario_id appears in the message's menciones array
 * (verified via mentionDisplayMap lookup).
 */
function renderContentWithMentions(
  content: string | null | undefined,
  menciones: { usuario_id: string }[],
  mentionDisplayMap: Map<string, MentionableUserSummary>,
): React.ReactNode[] {
  if (!content) return [];
  const mentionUserIds = new Set(menciones.map((m) => m.usuario_id));

  // Regex to match @username tokens (alphanumeric + underscores, min 1 char)
  const tokenRegex = /@(\w+)/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null = tokenRegex.exec(content);

  while (match !== null) {
    // Text before the mention
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }

    const token = match[0]; // e.g., "@admin"
    const username = match[1].toLowerCase();

    // Find if any user in mentionDisplayMap has this username
    let found = false;
    for (const [_id, user] of mentionDisplayMap) {
      if (user.username?.toLowerCase() === username) {
        // Verify this user was actually mentioned in this message
        if (mentionUserIds.has(user.id)) {
          const label = getMentionLabel(user);
          parts.push(
            <span
              key={`mention-${match.index}-${match[0]}`}
              className="inline-flex items-center gap-0.5 text-[10px] bg-primary/10 text-primary border border-primary/20 rounded px-1 py-0.5 font-medium"
            >
              @{label}
            </span>,
          );
          found = true;
          break;
        }
      }
    }

    // If not found in mentionDisplayMap or not in menciones, keep raw text
    if (!found) {
      parts.push(token);
    }

    lastIndex = match.index + match[0].length;
    match = tokenRegex.exec(content);
  }

  // Remaining text after last match
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [content];
}

/** Returns date string (YYYY-MM-DD) for date-change divider logic */
function getDateKey(fechaEnvio: string): string {
  return fechaEnvio.slice(0, 10);
}

// ── Main Component ─────────────────────────────────────────────────────────────

/**
 * Enriched mention map entry: full UsuarioMencionable data preserved so
 * getMentionContextLabel can compute the area/rol/ciclo context label.
 */
export interface EnrichedMentionEntry {
  /** Basic display fields — mirrors MentionableUserSummary for getMentionLabel compat. */
  id: string;
  username?: string;
  nombres?: string | null;
  apellidos?: string | null;
  dni?: string | null;
  /** Extended context fields (only present when fetched with solicitud_id). */
  area_nombre?: string | null;
  rol?: string | null;
  numero_ciclo?: number | null;
  tipo_participacion?: string | null;
}

export interface CommentThreadProps {
  mensajes: Mensaje[];
  /**
   * ID of the current authenticated user.
   * Accepts both the new nested shape (user.datos.id) and any stale
   * cookies/sessions that may carry the old flat user.id shape.
   */
  currentUserId?: string;
  onReply: (mensaje: Mensaje) => void;
  isDeleting?: boolean;
  onDelete?: (mensajeId: string) => void;
  /**
   * List of mentionable users for this conversation context.
   * CommentThread builds an internal Map<usuario_id, EnrichedMentionEntry>
   * to render historical mention labels AND area/role context instead of raw UUIDs.
   * When fetched with solicitud_id, entries include period context fields.
   */
  usuariosMencionables?: UsuarioMencionable[];
}

export function CommentThread({
  mensajes,
  currentUserId,
  onReply,
  isDeleting = false,
  onDelete,
  usuariosMencionables,
}: CommentThreadProps) {
  // Internal lookup map: usuario_id → enriched entry with context fields.
  // Built once when usuariosMencionables changes.
  const mentionDisplayMap = useMemo(() => {
    if (!usuariosMencionables) return new Map<string, EnrichedMentionEntry>();
    return new Map<string, EnrichedMentionEntry>(
      usuariosMencionables.map((u) => [
        u.id,
        {
          id: u.id,
          username: u.username,
          nombres: u.nombres,
          apellidos: u.apellidos,
          dni: u.dni,
          area_nombre: u.area_nombre,
          rol: u.rol,
          numero_ciclo: u.numero_ciclo,
          tipo_participacion: u.tipo_participacion,
        },
      ]),
    );
  }, [usuariosMencionables]);

  const tree = useMemo(() => {
    const map = new Map<string, MensajeTree>();
    const roots: MensajeTree[] = [];

    // First pass: create tree nodes
    mensajes.forEach((m) => {
      map.set(m.id, { ...m, children: [] });
    });

    // Second pass: build tree
    mensajes.forEach((m) => {
      const node = map.get(m.id);
      if (!node) return;

      if (m.mensaje_padre_id) {
        const parent = map.get(m.mensaje_padre_id);
        if (parent) {
          parent.children.push(node);
        } else {
          // Orphaned message (parent not in current page) — treat as root
          roots.push(node);
        }
      } else {
        roots.push(node);
      }
    });

    // Recursively sort all children arrays by fecha_envio ascending (chronological)
    const sortChildren = (nodes: MensajeTree[]): void => {
      nodes.sort(
        (a, b) =>
          new Date(a.fecha_envio).getTime() - new Date(b.fecha_envio).getTime(),
      );
      for (const node of nodes) {
        sortChildren(node.children);
      }
    };
    sortChildren(roots);

    return roots.sort(
      (a, b) =>
        new Date(a.fecha_envio).getTime() - new Date(b.fecha_envio).getTime(),
    );
  }, [mensajes]);

  // Compute date-change dividers: only when the calendar date shifts
  // Must be called unconditionally (before early return) to respect hooks rules
  const dateDividers = useMemo(() => {
    const dividers: boolean[] = new Array(tree.length).fill(false);
    for (let i = 1; i < tree.length; i++) {
      const prevDate = getDateKey(tree[i - 1].fecha_envio);
      const currDate = getDateKey(tree[i].fecha_envio);
      if (prevDate !== currDate) {
        dividers[i] = true;
      }
    }
    return dividers;
  }, [tree]);

  if (tree.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center gap-2">
        <p className="text-xs text-muted-foreground">No hay mensajes aún.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tree.map((rootMessage, index) => (
        <div key={rootMessage.id}>
          {dateDividers[index] && (
            <div className="flex items-center gap-2 mb-2">
              <div className="flex-1 h-px bg-border/40" />
              <span className="text-[9px] text-muted-foreground/50 uppercase tracking-wider">
                {rootMessage.autor_usuario_id
                  ? formatDateTime(rootMessage.fecha_envio).split(",")[0]
                  : "Sistema"}
              </span>
              <div className="flex-1 h-px bg-border/40" />
            </div>
          )}
          <ThreadItem
            message={rootMessage}
            level={0}
            currentUserId={currentUserId}
            onReply={onReply}
            isDeleting={isDeleting}
            onDelete={onDelete}
            mentionDisplayMap={mentionDisplayMap}
          />
        </div>
      ))}
    </div>
  );
}

// ── Recursive Item ─────────────────────────────────────────────────────────────

interface ThreadItemProps {
  message: MensajeTree;
  level: number;
  currentUserId?: string;
  onReply: (mensaje: Mensaje) => void;
  isDeleting: boolean;
  onDelete?: (mensajeId: string) => void;
  mentionDisplayMap: Map<string, EnrichedMentionEntry>;
}

function ThreadItem({
  message,
  level,
  currentUserId,
  onReply,
  isDeleting,
  onDelete,
  mentionDisplayMap,
}: ThreadItemProps) {
  // System/area response messages: identified by missing autor OR explicit SISTEMA tipo.
  // These are always treated as non-own, left-aligned, no reply support.
  const isSystemMessage =
    message.tipo === "SISTEMA" || message.autor_usuario_id == null;

  const isOwnMessage =
    !isSystemMessage &&
    currentUserId != null &&
    message.autor_usuario_id != null &&
    message.autor_usuario_id === currentUserId;

  const canReply = level < MAX_VISIBLE_DEPTH && !isSystemMessage;
  const hasChildren = message.children.length > 0;

  const autorData = mentionDisplayMap.get(message.autor_usuario_id ?? "");

  // Resolve author display name for prominent showing.
  // Priority: autor_nombre → mentionable full label → username → name-derived initials.
  // For own messages: show real name if available, fall back to "Tú" only
  // when no name data whatsoever exists. Preserves area/role/cycle context.
  // System/area messages: show "Sistema" or autor_nombre (area name) if available.
  const autorDisplay = isSystemMessage
    ? (message.autor_nombre ?? "Sistema")
    : (() => {
        // 1. Prefer autor_nombre if available (populated from backend join)
        if (message.autor_nombre) return message.autor_nombre;
        // 2. Fall back to mentionable lookup (works for own and other messages)
        if (autorData) return getMentionLabel(autorData);
        // 3. Fall back to autor_username if available
        if (message.autor_username) return `@${message.autor_username}`;
        // 4. Ultimate fallback — never UUID-derived; only "Tú" when nothing else exists
        return isOwnMessage ? "Tú" : "?";
      })();

  // Avatar initials come from the resolved name — never from a raw UUID slice.
  const initials = (() => {
    if (isSystemMessage) return "SY";
    const fullName = [autorData?.nombres, autorData?.apellidos]
      .filter((v): v is string => v != null && v.trim() !== "")
      .join(" ")
      .trim();
    if (fullName) return initialsFromName(fullName);
    if (message.autor_nombre) return initialsFromName(message.autor_nombre);
    if (message.autor_username) return initialsFromName(message.autor_username);
    return isOwnMessage ? "TU" : "?";
  })();

  // Resolve author context label (area · rol · ciclo N · Tipo) when available.
  // Shown for all messages including own messages when context data exists.
  // Not shown for system messages (autorContext is the area name already).
  const autorContext = (() => {
    if (isSystemMessage) return null;
    if (!autorData) return null;
    return getMentionContextLabel(
      autorData as unknown as import("../schemas").UsuarioMencionable,
    );
  })();

  // Parse content with inline mention chips
  const contentWithMentions = useMemo(
    () =>
      renderContentWithMentions(
        message.contenido,
        message.menciones,
        mentionDisplayMap,
      ),
    [message.contenido, message.menciones, mentionDisplayMap],
  );

  // Indent visual hierarchy: any message at level > 0 is a reply and must be
  // indented with a left border to make nesting visually clear — regardless of
  // whether that reply itself has children (leaf replies still need the indent).
  return (
    <div className={level > 0 ? "ml-8 pl-2 border-l-2 border-border/50" : ""}>
      {/*
        Compact chat bubble row:
        - Avatar and bubble share a flex group; group flips for own messages (flex-row-reverse)
        - Bubble max-width constrained so it doesn't span full container width
        - Header (name/date) sits above bubble inside the content block
        - Actions sit below bubble, under the content block
        - System/area messages are always left-aligned with distinct bubble styling
      */}
      <div
        className={cn(
          "group/message flex items-start gap-2",
          isSystemMessage && "flex-row",
        )}
      >
        {/* Avatar — adjacent to bubble, not at far edge.
            System messages use a distinct muted avatar style. */}
        <Avatar
          className={cn(
            "w-7 h-7 shrink-0 mt-0.5",
            isSystemMessage
              ? "border border-muted-foreground/20 bg-muted/30"
              : "border border-border",
          )}
          size="sm"
        >
          <AvatarFallback
            className={cn(
              "text-[10px] font-bold",
              isSystemMessage
                ? "bg-muted text-muted-foreground"
                : "bg-primary/10 text-primary",
            )}
          >
            {initials}
          </AvatarFallback>
        </Avatar>

        {/* Content block: header + bubble + actions */}
        <div
          className={cn(
            "flex flex-col gap-0.5 min-w-0 max-w-[min(38rem,85%)]",
            "items-start",
          )}
        >
          {/* Header: author + context + date, left-aligned */}
          <div
            className={cn("flex items-center gap-1.5 flex-wrap", "flex-row")}
          >
            <span
              className={cn(
                "text-[10px] font-medium",
                isSystemMessage
                  ? "text-muted-foreground"
                  : "text-foreground/70",
              )}
            >
              {autorDisplay}
            </span>
            {autorContext && (
              <span className="text-[10px] text-muted-foreground/60 italic">
                {autorContext}
              </span>
            )}
            <span className="text-[10px] text-muted-foreground">
              {formatDateTime(message.fecha_envio)}
            </span>
            {message.editado_at && (
              <span className="text-[10px] text-muted-foreground italic">
                (editado)
              </span>
            )}
          </div>

          {/* Bubble: constrained width, not full width.
              System messages use a distinct muted style (no user-bubble border). */}
          <div
            className={cn(
              "rounded-lg p-2.5 min-w-0 max-w-[min(38rem,85%)]",
              isSystemMessage
                ? "bg-muted/20 border border-muted-foreground/10 rounded-tl-none"
                : cn("bg-muted/40 border border-border/50", "rounded-tl-none"),
            )}
          >
            {/* Text content with inline mention chips */}
            {contentWithMentions.length > 0 && (
              <p
                className="text-sm text-foreground/90 whitespace-pre-wrap break-words"
                style={{
                  overflowWrap: "anywhere",
                  wordBreak: "break-word",
                }}
              >
                {contentWithMentions}
              </p>
            )}

            {/* Attachments rendered inside bubble as visual extension */}
            {message.archivos_adjuntos.length > 0 && (
              <div className="flex flex-col gap-1 mt-2 pt-2 border-t border-border/30">
                {message.archivos_adjuntos.map((adj) => (
                  <div key={adj.id} className="flex flex-col gap-0.5">
                    <a
                      href={adj.archivo_url ?? "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-[11px] text-primary bg-primary/5 border border-primary/10 px-2 py-1 rounded hover:bg-primary/10 transition-colors self-start"
                      download={adj.nombre_original}
                    >
                      <Paperclip className="w-3 h-3 shrink-0" />
                      <span className="truncate max-w-[160px]">
                        {adj.nombre_original}
                      </span>
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

          {/* Actions: aligned under bubble block, left-aligned */}
          <div className={cn("flex items-center gap-2", "flex-row")}>
            {canReply && (
              <button
                type="button"
                onClick={() => onReply(message)}
                className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
              >
                <Reply className="w-3 h-3" />
                Responder
              </button>
            )}
            {isOwnMessage && onDelete && (
              <button
                type="button"
                onClick={() => onDelete(message.id)}
                disabled={isDeleting}
                className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-destructive transition-colors"
              >
                Eliminar
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Children — only render indent + children when there are actual children */}
      {hasChildren && level < MAX_VISIBLE_DEPTH && (
        <div className="mt-0.5">
          {message.children
            .sort(
              (a, b) =>
                new Date(a.fecha_envio).getTime() -
                new Date(b.fecha_envio).getTime(),
            )
            .map((child) => (
              <ThreadItem
                key={child.id}
                message={child}
                level={level + 1}
                currentUserId={currentUserId}
                onReply={onReply}
                isDeleting={isDeleting}
                onDelete={onDelete}
                mentionDisplayMap={mentionDisplayMap}
              />
            ))}
        </div>
      )}
    </div>
  );
}
