"use client";

import { CheckCircle, FileText, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { notify } from "@/errors";
import { useFinalizarSolicitud } from "../hooks/useFinalizarSolicitud";
import {
  type FinalizarSolicitudFormData,
  TIPO_RESPUESTA_LABELS,
  type TipoRespuesta,
} from "../schemas/finalizar-solicitud.schema";

interface FinalizarSolicitudModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  solicitudId: string;
  /** Disable if user is not in any area that can respond */
  disabled?: boolean;
  onSuccess?: () => void;
}

export function FinalizarSolicitudModal({
  open,
  onOpenChange,
  solicitudId,
  disabled = false,
  onSuccess,
}: FinalizarSolicitudModalProps) {
  const finalizarMutation = useFinalizarSolicitud(solicitudId);

  const [tipoRespuesta, setTipoRespuesta] = useState<TipoRespuesta | "">("");
  const [contenido, setContenido] = useState("");
  const [files, setFiles] = useState<File[]>([]);

  const resetForm = useCallback(() => {
    setTipoRespuesta("");
    setContenido("");
    setFiles([]);
  }, []);

  useEffect(() => {
    if (!open) {
      resetForm();
    }
  }, [open, resetForm]);

  const handleClose = useCallback(
    (newOpen: boolean) => {
      if (!newOpen) {
        resetForm();
      }
      onOpenChange(newOpen);
    },
    [onOpenChange, resetForm],
  );

  const handleSubmit = useCallback(async () => {
    if (!tipoRespuesta) {
      notify.error("Selecciona un tipo de respuesta");
      return;
    }
    if (!contenido.trim()) {
      notify.error("El contenido de la respuesta es requerido");
      return;
    }

    const formData: FinalizarSolicitudFormData = {
      tipo_respuesta: tipoRespuesta as TipoRespuesta,
      contenido: contenido.trim(),
      archivos: files.map((file) => ({
        file,
        nombre_original: file.name,
        mime_type: file.type || null,
        tamano_bytes: file.size,
      })),
    };

    try {
      await finalizarMutation.mutateAsync(formData);
      notify.success("Respuesta formal emitida correctamente");
      resetForm();
      onSuccess?.();
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  }, [
    tipoRespuesta,
    contenido,
    files,
    finalizarMutation,
    resetForm,
    onSuccess,
    onOpenChange,
  ]);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = Array.from(e.target.files ?? []);
      setFiles((prev) => [...prev, ...selected]);
    },
    [],
  );

  const handleRemoveFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const isPending = finalizarMutation.isPending;

  return (
    <GenericModal open={open} onOpenChange={handleClose} preventClose={false}>
      <GenericModal.Content size="md">
        <GenericModal.Header className="bg-primary/[0.03] border-b border-border px-6 py-5">
          <div className="flex items-center gap-3 w-full">
            <div className="p-2 rounded-xl border border-primary/20 shadow-sm bg-primary/10">
              <CheckCircle className="h-5 w-5 text-primary" />
            </div>
            <div className="flex flex-col gap-0.5 min-w-0 flex-1">
              <span className="hidden sm:block text-[10px] font-bold uppercase tracking-widest text-primary leading-none">
                Respuesta Formal
              </span>
              <h2 className="text-2xl font-black tracking-tight text-foreground leading-tight">
                Finalizar Solicitud
              </h2>
              <p className="hidden sm:block text-sm text-muted-foreground leading-relaxed">
                Registra la respuesta formal institucional y cierra la solicitud
              </p>
            </div>
            <div className="w-9 shrink-0" aria-hidden="true" />
          </div>
        </GenericModal.Header>

        <GenericModal.Body className="space-y-5">
          {/* Tipo de respuesta */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Tipo de respuesta
            </label>
            <Select
              value={tipoRespuesta}
              onValueChange={(v) => setTipoRespuesta(v as TipoRespuesta)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecciona el tipo de respuesta..." />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TIPO_RESPUESTA_LABELS) as TipoRespuesta[]).map(
                  (tipo) => (
                    <SelectItem key={tipo} value={tipo}>
                      {TIPO_RESPUESTA_LABELS[tipo]}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
          </div>

          {/* Contenido */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Contenido de la respuesta
              <span className="text-destructive ml-1">*</span>
            </label>
            <Textarea
              value={contenido}
              onChange={(e) => setContenido(e.target.value)}
              placeholder="Describe la respuesta formal a la solicitud..."
              rows={5}
              maxLength={5000}
            />
            <p className="text-xs text-muted-foreground text-right">
              {contenido.length} / 5000
            </p>
          </div>

          {/* Archivos adjuntos */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Archivos adjuntos
              <span className="text-muted-foreground font-normal ml-1">
                (opcional)
              </span>
            </label>
            <div className="border border-dashed border-border rounded-xl p-4 space-y-3">
              {files.length > 0 && (
                <ul className="space-y-2">
                  {files.map((file, index) => (
                    <li
                      key={index}
                      className="flex items-center justify-between gap-2 bg-muted/50 rounded-lg px-3 py-2"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="text-sm truncate">{file.name}</span>
                        <span className="text-xs text-muted-foreground shrink-0">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFile(index)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <label className="flex items-center justify-center gap-2 cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors">
                <input
                  type="file"
                  multiple
                  className="sr-only"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
                />
                <span>Adjuntar archivos</span>
              </label>
            </div>
          </div>
        </GenericModal.Body>

        <GenericModal.Footer className="px-6 py-4 bg-muted/30 border-t border-border">
          <div className="flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={isPending}
              className="h-10 rounded-xl font-semibold"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isPending || disabled}
              className="h-10 rounded-xl font-bold gap-1.5"
            >
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Emitir Respuesta
            </Button>
          </div>
        </GenericModal.Footer>

        <GenericModal.CloseX />
      </GenericModal.Content>
    </GenericModal>
  );
}
