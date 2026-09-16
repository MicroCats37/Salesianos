"use client";

import {
  type ChangeEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import { cn } from "@/lib/utils";

export interface ChatTextareaProps {
  /** Controlled value */
  value: string;
  /** Called when the user types */
  onValueChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  /** Called on Ctrl+Enter / Cmd+Enter */
  onKeyDown?: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  /** Called when @query is typed after @ — use for mention search */
  onMentionSearch?: (query: string) => void;
  className?: string;
}

/**
 * Auto-growing textarea styled like a shadcn Textarea.
 *
 * Uses a mirror-div technique for reliable auto-growth measurement.
 * Handles @mention detection by calling `onMentionSearch` with the query
 * after the `@` trigger character.
 *
 * Min height: 80px (≈4 lines). Max height: 256px with overflow scroll.
 * Naturally stops growing at max-height — user can scroll within.
 */
export function ChatTextarea({
  value,
  onValueChange,
  placeholder,
  disabled,
  onKeyDown,
  onMentionSearch,
  className,
}: ChatTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mirrorRef = useRef<HTMLDivElement>(null);
  const mentionTriggerRef = useRef<string | null>(null);
  const [isFocused, setIsFocused] = useState(false);
  const id = useId();

  // Sync mirror content + measure height every time value changes
  const syncMirror = useCallback(() => {
    const mirror = mirrorRef.current;
    const textarea = textareaRef.current;
    if (!mirror || !textarea) return;

    // Keep mirror in sync with textarea content + styling
    mirror.textContent = `${value || ""}\n`;
    const mirrorHeight = mirror.scrollHeight;
    const minHeight = 80;
    const maxHeight = 256;

    const computedHeight = Math.min(
      Math.max(mirrorHeight, minHeight),
      maxHeight,
    );
    textarea.style.height = `${computedHeight}px`;
    textarea.style.overflowY = mirrorHeight > maxHeight ? "auto" : "hidden";
  }, [value]);

  useLayoutEffect(() => {
    syncMirror();
  }, [syncMirror]);

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      onValueChange(newValue);

      // Detect @mention trigger
      const match = newValue.match(/@(\w*)$/);
      if (match) {
        mentionTriggerRef.current = match[0]; // e.g. "@jo" or "@"
        onMentionSearch?.(match[1]);
      } else {
        mentionTriggerRef.current = null;
      }
    },
    [onValueChange, onMentionSearch],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Ctrl/Cmd + Enter → submit
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        onKeyDown?.(e);
        return;
      }
      onKeyDown?.(e);
    },
    [onKeyDown],
  );

  // Focus the textarea on mount (for reply)
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <div className="relative w-full">
      {/* Hidden mirror div — same font/padding/width as textarea, invisible, measures content */}
      <div
        ref={mirrorRef}
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-words border border-transparent p-[calc(0.625rem-1px)] text-sm leading-6 opacity-0"
        style={{ fontFamily: "inherit", fontSize: "14px" }}
      />

      {/* Actual textarea */}
      <textarea
        ref={textareaRef}
        id={id}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          // Base: field-sizing-content + border/padding to match shadcn Textarea
          "flex w-full min-w-0 rounded-lg border border-input bg-background px-3 py-2.5 text-sm leading-6",
          "placeholder:text-muted-foreground",
          "transition-colors",
          "focus-visible:outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-input/50",
          "resize-none box-border align-baseline",
          // Text wrapping: break-words ensures unbroken strings wrap
          "break-words overflow-x-hidden whitespace-pre-wrap",
          // Auto-grow constraints — must match mirror measurement
          "min-h-[80px] max-h-[256px] overflow-y-hidden",
          // Focus ring highlight
          isFocused && "border-ring ring-3 ring-ring/50 border-primary/60",
          className,
        )}
        style={{
          // Critical for auto-grow: inherit font metrics from parent
          fontFamily: "inherit",
          fontSize: "14px",
          lineHeight: "24px",
          // Ensure field-sizing doesn't cap us
          fieldSizing: "content",
          // Overflow-wrap: anywhere forces wrapping on any breakpoint
          overflowWrap: "anywhere",
        }}
      />
    </div>
  );
}
