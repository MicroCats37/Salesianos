// genericForm/inputs/InputFileCollection.tsx
// Smart Field para subida y gestión de archivos.
// Organiza archivos en secciones: Documento Principal (1) y Anexos (N).
// Dentro de Anexos separa: Imágenes y Documentos.
// NO contiene validación interna — Zod la maneja.
// Usa useController de RHF.

"use client";

import {
  FileIcon,
  FileText,
  ImageIcon,
  Paperclip,
  Upload,
  X,
} from "lucide-react";
import type React from "react";
import { useRef } from "react";
import { useController } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { notify } from "@/errors";
import { cn } from "@/lib/utils";
import {
  TIPO_ARCHIVO,
  type TipoArchivo,
} from "@/shared/constants/tramite.tokens";
import type { InputComponentProps } from "./types";

// ── Tipos internos ─────────────────────────────────────────────────────────────

export interface ArchivoItem {
  /** ID único del archivo en el formulario */
  id: string;
  /** Objeto File del navegador */
  file: File;
  /** Tipo: PRINCIPAL o ANEXO */
  tipo_archivo: TipoArchivo;
  /** Nombre original del archivo */
  nombre_original: string;
  /** Descripción opcional */
  descripcion?: string;
}

export interface InputFileCollectionProps extends InputComponentProps {
  /** Máximo número de archivos (default: 10) */
  maxFiles?: number;
  /** Tipos MIME aceptados, ej: ".pdf,.jpg,.png" (default: todos) */
  allowedTypes?: string;
  /**
   * Restricción de tipo de archivo:
   * - "principal": solo permite archivos PRINCIPAL (usuario no elige tipo)
   * - "anexo": solo permite archivos ANEXO (usuario no elige tipo)
   * - "all": usuario elige por archivo (default)
   */
  fileKind?: "principal" | "anexo" | "all";
}

// ── Utilidades ─────────────────────────────────────────────────────────────────

function getFileIcon(file: File): React.ReactNode {
  const type = file.type;
  if (type.startsWith("image/")) return <ImageIcon className="w-4 h-4" />;
  if (type === "application/pdf") return <Paperclip className="w-4 h-4" />;
  return <FileText className="w-4 h-4" />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function buildInitialValue(value: unknown): ArchivoItem[] {
  if (!value) return [];
  if (Array.isArray(value)) return value as ArchivoItem[];
  // Compatible con el shape { principal: [], anexo: [] } del backend
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const principal = Array.isArray(obj.principal) ? obj.principal : [];
    const anexo = Array.isArray(obj.anexo) ? obj.anexo : [];
    return [
      ...(principal as ArchivoItem[]),
      ...(anexo as ArchivoItem[]),
    ].filter((item): item is ArchivoItem => item != null && item.id != null);
  }
  return [];
}

// ── Sub-componente: FileCard ───────────────────────────────────────────────────

interface FileCardProps {
  archivo: ArchivoItem;
  showTipoSelector: boolean;
  onRemove: (id: string) => void;
  onDescripcionChange: (id: string, descripcion: string) => void;
  error?: boolean;
}

const FileCard: React.FC<FileCardProps> = ({
  archivo,
  showTipoSelector,
  onRemove,
  onDescripcionChange,
  error,
}) => {
  const tipoToken = TIPO_ARCHIVO[archivo.tipo_archivo];

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-lg border p-3 bg-muted/20",
        error ? "border-destructive/50" : "border-border",
      )}
    >
      {/* Fila principal: icono, nombre, tamaño, badge, acciones */}
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 text-muted-foreground">
          {getFileIcon(archivo.file)}
        </div>

        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-medium truncate"
            title={archivo.nombre_original}
          >
            {archivo.nombre_original}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatFileSize(archivo.file.size)}
          </p>
        </div>

        {/* Badge tipo archivo */}
        <span
          className={cn(
            "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border",
            tipoToken.badgeClass,
          )}
        >
          {tipoToken.label}
        </span>

        {/* Botón quitar */}
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          className="flex-shrink-0 text-muted-foreground hover:text-destructive"
          onClick={() => onRemove(archivo.id)}
          title="Quitar archivo"
        >
          <X className="w-3.5 h-3.5" />
        </Button>
      </div>

      {/* Input descripción */}
      {archivo.descripcion !== undefined && (
        <div>
          <input
            type="text"
            placeholder="Descripción (opcional)"
            value={archivo.descripcion || ""}
            onChange={(e) => onDescripcionChange(archivo.id, e.target.value)}
            className="w-full h-7 text-xs rounded border border-input bg-background px-2 py-1 placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-ring"
          />
        </div>
      )}
    </div>
  );
};

// ── Componente principal ───────────────────────────────────────────────────────

export const InputFileCollection: React.FC<InputFileCollectionProps> = ({
  field,
  control,
  id,
  hideErrorMessage,
  error,
  maxFiles = 10,
  allowedTypes,
  fileKind = "all",
}) => {
  const {
    field: { onChange, value },
  } = useController({ name: field.name, control });

  const files: ArchivoItem[] = buildInitialValue(value);
  const principalInputRef = useRef<HTMLInputElement>(null);
  const anexosInputRef = useRef<HTMLInputElement>(null);
  const internalId = id || `file-collection-${field.name}`;

  // Separar principal y anexos
  const principalFile = files.filter((f) => f.tipo_archivo === "PRINCIPAL");
  const anexoFiles = files.filter((f) => f.tipo_archivo === "ANEXO");

  // Dentro de anexos: imágenes vs documentos
  const imagenFiles = anexoFiles.filter((f) =>
    f.file.type.startsWith("image/"),
  );
  const documentoFiles = anexoFiles.filter(
    (f) => !f.file.type.startsWith("image/"),
  );

  const showTipoSelector = fileKind === "all";
  const acceptValue = allowedTypes || "*/*";
  const canAddMore = files.length < maxFiles;

  const createLocalFileId = () =>
    `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  const handlePrincipalChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    // El principal es solo 1 archivo. Si el usuario selecciona varios,
    // tomamos el primero y notificamos (la validación de Zod se encarga del resto).
    if (selectedFiles.length > 1) {
      notify.error(
        `Solo se permite un documento principal — se tomó el primero: ${selectedFiles[0].name}`,
      );
    }

    const newFile: ArchivoItem = {
      id: createLocalFileId(),
      file: selectedFiles[0],
      tipo_archivo: "PRINCIPAL",
      nombre_original: selectedFiles[0].name,
      descripcion: "",
    };

    // Reemplazar principal existente o agregar
    const withoutPrincipal = files.filter(
      (f) => f.tipo_archivo !== "PRINCIPAL",
    );
    onChange([...withoutPrincipal, newFile]);

    if (principalInputRef.current) principalInputRef.current.value = "";
  };

  const handleAnexosChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    const currentAnexosCount = anexoFiles.length;
    const remainingSlots = maxFiles - currentAnexosCount;
    if (remainingSlots <= 0) {
      notify.error(`Se alcanzó el máximo de ${maxFiles} archivos`);
      if (anexosInputRef.current) anexosInputRef.current.value = "";
      return;
    }

    // El usuario puede seleccionar varios archivos a la vez.
    // Si excede el límite, tomamos solo los que caben.
    const filesToAdd = selectedFiles.slice(0, remainingSlots);

    const newItems: ArchivoItem[] = filesToAdd.map((file) => ({
      id: createLocalFileId(),
      file,
      tipo_archivo: "ANEXO" as TipoArchivo,
      nombre_original: file.name,
      descripcion: "",
    }));

    const withoutAnexos = files.filter((f) => f.tipo_archivo !== "ANEXO");
    onChange([...withoutAnexos, ...newItems]);

    if (selectedFiles.length > remainingSlots) {
      notify.error(
        `Se agregaron ${filesToAdd.length} de ${selectedFiles.length} archivos (límite: ${maxFiles})`,
      );
    }

    if (anexosInputRef.current) anexosInputRef.current.value = "";
  };

  const handleRemoveFile = (idToRemove: string) => {
    onChange(files.filter((f) => f.id !== idToRemove));
  };

  const handleDescripcionChange = (id: string, descripcion: string) => {
    onChange(files.map((f) => (f.id === id ? { ...f, descripcion } : f)));
  };

  return (
    <div className="space-y-4">
      {/* ── Contenedor principal ── */}
      <div className="rounded-lg border border-dashed p-4 space-y-4">
        <div className="flex items-center gap-2">
          <FileIcon className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Archivos del Trámite</span>
        </div>

        {/* ── Sección: Documento Principal ── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">
              Documento Principal
              {principalFile.length > 0 && (
                <span className="ml-1 text-xs font-normal text-muted-foreground">
                  ({principalFile.length})
                </span>
              )}
            </span>
          </div>

          {/* Card con archivo principal o input vacío */}
          {principalFile.length > 0 ? (
            <FileCard
              archivo={principalFile[0]}
              showTipoSelector={showTipoSelector}
              onRemove={handleRemoveFile}
              onDescripcionChange={handleDescripcionChange}
              error={!!error}
            />
          ) : (
            <div
              className={cn(
                "flex flex-col items-center justify-center rounded-lg border p-4 cursor-pointer hover:border-ring transition-colors",
                error ? "border-destructive/50" : "border-border",
              )}
              onClick={() =>
                document.getElementById(`${internalId}-principal`)?.click()
              }
            >
              <Upload className="w-5 h-5 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground text-center">
                Subir documento principal
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                PDF, DOC, DOCX, XLS, XLSX — máx. 1 archivo
              </p>
            </div>
          )}

          <input
            id={`${internalId}-principal`}
            ref={principalInputRef}
            type="file"
            accept={acceptValue}
            className="hidden"
            onChange={handlePrincipalChange}
          />
        </div>

        {/* ── Sección: Anexos ── */}
        <div className="space-y-2 pt-2 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">
              Anexos
              {anexoFiles.length > 0 && (
                <span className="ml-1 text-xs font-normal text-muted-foreground">
                  ({anexoFiles.length})
                </span>
              )}
            </span>
            {canAddMore && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  document.getElementById(`${internalId}-anexos`)?.click()
                }
                className="gap-2"
              >
                <Upload className="w-3.5 h-3.5" />
                Añadir anexo
              </Button>
            )}
          </div>

          <input
            id={`${internalId}-anexos`}
            ref={anexosInputRef}
            type="file"
            accept={acceptValue}
            multiple
            className="hidden"
            onChange={handleAnexosChange}
          />

          {/* Drop zone cuando no hay anexos */}
          {anexoFiles.length === 0 && canAddMore && (
            <div
              className="flex flex-col items-center justify-center rounded-lg border border-dashed p-4 cursor-pointer hover:border-ring transition-colors"
              onClick={() =>
                document.getElementById(`${internalId}-anexos`)?.click()
              }
            >
              <Upload className="w-5 h-5 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground text-center">
                Arrastre archivos aquí o haga clic para seleccionar
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Imágenes, PDF, DOC, XLS — múltiples archivos
              </p>
            </div>
          )}

          {/* Sub-sección: Imágenes */}
          {imagenFiles.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <ImageIcon className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Imágenes
                </span>
              </div>
              <div className="grid gap-2">
                {imagenFiles.map((archivo) => (
                  <FileCard
                    key={archivo.id}
                    archivo={archivo}
                    showTipoSelector={showTipoSelector}
                    onRemove={handleRemoveFile}
                    onDescripcionChange={handleDescripcionChange}
                    error={!!error}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Sub-sección: Documentos */}
          {documentoFiles.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Documentos
                </span>
              </div>
              <div className="grid gap-2">
                {documentoFiles.map((archivo) => (
                  <FileCard
                    key={archivo.id}
                    archivo={archivo}
                    showTipoSelector={showTipoSelector}
                    onRemove={handleRemoveFile}
                    onDescripcionChange={handleDescripcionChange}
                    error={!!error}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contador */}
      {maxFiles < 100 && (
        <p className="text-xs text-muted-foreground">
          {files.length} / {maxFiles} archivos
        </p>
      )}

      {/* Error — solo si hideErrorMessage es false */}
      {!hideErrorMessage && error && (
        <p className="text-sm text-destructive font-medium">{error.message}</p>
      )}
    </div>
  );
};
