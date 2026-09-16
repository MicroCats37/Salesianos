/**
 * SmartAttachmentField — chat-style file attachment field for message composer.
 *
 * UX (chat-style):
 *   - Trigger button to select files
 *   - Attachment chips with file name + remove button
 *   - Simple inline size validation (10 MB default)
 *
 * Public API:
 *   - anexos: File[] — current selected files
 *   - onChange: (files: File[]) => void
 *   - isSubmitting: disable controls during submission
 *   - maxFileSizeMb: optional size limit
 *
 * Note: Unlike the reference SmartAnexoField (for eventos with per-file metadata),
 * conversaciones only need raw File objects — the backend stores only
 * archivo_url, nombre_original, mime_type, tamano_bytes.
 * No metadata editor dialog is needed.
 */
"use client";

import { Paperclip, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DEFAULT_MAX_SIZE_MB = 10;

interface SmartAttachmentFieldProps {
  anexos: File[];
  onChange: (files: File[]) => void;
  isSubmitting?: boolean;
  maxFileSizeMb?: number;
  /** Called by parent to trigger file selection */
  onAttachClick?: () => void;
}

export function SmartAttachmentField({
  anexos,
  onChange,
  isSubmitting = false,
  maxFileSizeMb = DEFAULT_MAX_SIZE_MB,
}: SmartAttachmentFieldProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sizeError, setSizeError] = useState<string | null>(null);

  const maxBytes = maxFileSizeMb * 1024 * 1024;

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (files.length === 0) return;

      const validFiles: File[] = [];
      let error: string | null = null;

      for (const file of files) {
        if (file.size > maxBytes) {
          error = `El archivo "${file.name}" excede ${maxFileSizeMb} MB`;
        } else {
          validFiles.push(file);
        }
      }

      if (error) {
        setSizeError(error);
      } else {
        setSizeError(null);
        onChange([...anexos, ...validFiles]);
      }

      // Reset so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [anexos, maxBytes, maxFileSizeMb, onChange],
  );

  const handleRemove = (index: number) => {
    onChange(anexos.filter((_, i) => i !== index));
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Attachment chips */}
      {anexos.length > 0 && (
        <div className="flex flex-wrap gap-1.5 min-w-0">
          {anexos.map((file, index) => (
            <div
              key={`${file.name}-${file.size}-${index}`}
              className={cn(
                "flex items-center gap-1 min-w-0 rounded-md px-2 py-1 text-xs",
                "bg-muted/60 border border-border/60 text-foreground",
              )}
            >
              <Paperclip className="w-3 h-3 shrink-0 text-muted-foreground" />
              <span className="truncate max-w-[120px]" title={file.name}>
                {file.name}
              </span>
              <button
                type="button"
                onClick={() => handleRemove(index)}
                disabled={isSubmitting}
                className="text-muted-foreground hover:text-destructive transition-colors shrink-0"
                aria-label={`Quitar ${file.name}`}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Size error */}
      {sizeError && <p className="text-[10px] text-destructive">{sizeError}</p>}

      {/* Attach button */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={triggerFileSelect}
        disabled={isSubmitting}
        className="h-8 w-8 p-0 shrink-0 text-muted-foreground hover:text-foreground"
        title="Adjuntar archivos"
      >
        <Paperclip className="w-4 h-4" />
      </Button>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="*/*"
        onChange={handleFileChange}
        className="hidden"
        disabled={isSubmitting}
      />
    </div>
  );
}
