// genericForm/inputs/InputImage.tsx
"use client";

import { ExternalLink, ImageIcon, Upload, X } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useController } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { resolveImageUrl } from "@/lib/utils";
import type { InputComponentProps } from "./types";

/**
 * The MIME allowlist and the size cap are the ones of the backend media
 * contract (`core/media.py`): the browser never accepts a file that the
 * server is going to reject.
 */
const ACCEPTED_MIME_TYPES = "image/jpeg,image/png,image/webp";
const MAX_SIZE_LABEL = "5 MiB";

/**
 * Input para imágenes con previsualización.
 * Maneja archivos individuales.
 *
 * The value of the form is the ONLY source of truth: the image that the
 * record already stores arrives as a URL through `initialData` and is
 * re-hydrated by the form, so the preview follows the form and never the
 * static configuration of the field.
 */
export const InputImage: React.FC<InputComponentProps> = ({
  field,
  control,
  error,
  id,
  errorId,
}) => {
  const {
    field: { onChange, onBlur, value },
  } = useController({ name: field.name, control });

  const internalId = id || `image-upload-${field.name}`;

  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  // La previsualización sigue el valor del formulario.
  useEffect(() => {
    let cancelled = false;

    if (value instanceof File) {
      setFileName(value.name);
      const reader = new FileReader();
      reader.onloadend = () => {
        if (!cancelled) setPreview(reader.result as string);
      };
      reader.readAsDataURL(value);
      return () => {
        cancelled = true;
      };
    }

    if (typeof value === "string" && value.length > 0) {
      // La imagen que el registro ya almacena.
      setFileName(value.split("/").pop() || null);
      setPreview(resolveImageUrl(value));
      return;
    }

    // Sin valor: no hay previsualización.
    setPreview(null);
    setFileName(null);
  }, [value]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // El formulario guarda el ARCHIVO, no un FileList: el transporte
      // construye el multipart, nunca el formulario.
      onChange(file);
    }
  };

  const clearImage = () => {
    // `null` es un valor explícito: limpia la imagen del registro.
    onChange(null);
    const input = document.getElementById(
      internalId,
    ) as HTMLInputElement | null;
    if (input) input.value = "";
  };

  return (
    <div className="space-y-3">
      <div
        className={`relative group border-2 border-dashed rounded-2xl overflow-hidden transition-all flex flex-col items-center justify-center min-h-[160px] bg-muted/5 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 ${
          error
            ? "border-destructive/50"
            : "border-muted-foreground/20 hover:border-primary/50"
        }`}
      >
        {preview ? (
          <div className="relative w-full h-full min-h-[160px]">
            <img
              src={preview}
              alt={field.label}
              className="w-full h-full object-cover max-h-[300px]"
            />
          </div>
        ) : (
          <label
            htmlFor={internalId}
            className="w-full h-full p-8 flex flex-col items-center justify-center gap-3 text-muted-foreground hover:text-primary transition-colors cursor-pointer"
          >
            <div className="p-4 bg-primary/5 rounded-full group-hover:bg-primary/10 transition-colors">
              <ImageIcon className="w-8 h-8" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-sm">
                Haga clic para subir una imagen
              </p>
              <p className="text-xs opacity-70 mt-1">
                JPG, PNG o WEBP (máx. {MAX_SIZE_LABEL})
              </p>
            </div>
          </label>
        )}

        {/* El control real: oculto visualmente pero alcanzable con el teclado. */}
        <input
          id={internalId}
          type="file"
          accept={ACCEPTED_MIME_TYPES}
          className="sr-only"
          onChange={handleFileChange}
          onBlur={onBlur}
          aria-label={field.label}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
        />
      </div>

      {/*
        The actions are ALWAYS visible: an action that only appears on hover
        is unreachable with a keyboard and unusable with a touch screen.
      */}
      <div className="flex flex-wrap items-center gap-2">
        <label
          htmlFor={internalId}
          className="inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium border border-input bg-background px-3 py-2 h-9 cursor-pointer hover:bg-accent hover:text-accent-foreground"
        >
          <Upload className="w-4 h-4" />
          {preview ? "Cambiar" : "Subir imagen"}
        </label>

        {preview && (
          <>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => window.open(preview, "_blank")}
              title="Ver imagen original"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Ver
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={clearImage}
            >
              <X className="w-4 h-4 mr-2" />
              Quitar
            </Button>
          </>
        )}
      </div>

      {fileName && !error && (
        <p className="text-[10px] font-mono text-muted-foreground bg-muted/30 px-2 py-1 rounded truncate">
          Archivo: {fileName}
        </p>
      )}
    </div>
  );
};
