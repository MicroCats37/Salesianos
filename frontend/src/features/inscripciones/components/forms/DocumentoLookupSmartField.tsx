"use client";

import { useEffect, useRef } from "react";
import { Search, Loader2 } from "lucide-react";
import { useFormContext, useWatch, Controller } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn, stripNonDigits } from "@/lib/utils";
import { useDocumentoLookup } from "../../hooks/useDocumentoLookup";

/**
 * Smart field que reemplaza el campo "numeroDocumento" en el formulario genérico.
 * Implementa la misma lógica estricta que RegisterForm: límite de caracteres,
 * bloqueo físico y el botón de búsqueda integrado.
 */
export function DocumentoLookupSmartField() {
  const {
    control,
    formState: { errors },
    setValue,
    trigger,
  } = useFormContext();
  const documentoLookup = useDocumentoLookup();

  // Escuchamos los campos relevantes
  const tipoDocumento = useWatch({ control, name: "tipoDocumento" }) ?? "DNI";
  const numeroDocumento = useWatch({ control, name: "numeroDocumento" }) ?? "";
  
  // Como estamos en un GenericForm, los errores pueden ser cualquier cosa. Forzamos a string
  const rawError = errors.numeroDocumento?.message;
  const error = typeof rawError === "string" ? rawError : undefined;

  // Lógica de límites y placeholders igual a RegisterForm
  const maxLen = tipoDocumento === "DNI" ? 8 : tipoDocumento === "CE" ? 9 : 20;
  const placeholder =
    tipoDocumento === "DNI"
      ? "12345678"
      : tipoDocumento === "CE"
        ? "123456789"
        : "ABC123456";
  const inputMode = tipoDocumento === "PAS" ? "text" : "numeric";
  const numStr = String(numeroDocumento).trim();
  const canLookup = tipoDocumento === "DNI" && numStr.length === 8;

  // Limpiar campos si cambia el tipo de documento
  const prevTipoRef = useRef(tipoDocumento);
  useEffect(() => {
    if (prevTipoRef.current !== tipoDocumento) {
      prevTipoRef.current = tipoDocumento;
      setValue("numeroDocumento", "", { shouldValidate: true });
      setValue("nombres", "", { shouldValidate: false });
      setValue("apellidos", "", { shouldValidate: false });
    }
  }, [tipoDocumento, setValue]);

  async function handleLookup() {
    const valid = await trigger("numeroDocumento");
    if (!valid || !canLookup) return;
    
    try {
      const result = await documentoLookup.mutateAsync(numStr);
      if (result) {
        if (!result.nombres || !result.apellidos) {
          toast.error("La respuesta no contiene nombres completos");
          return;
        }
        setValue("numeroDocumento", result.numero_documento, { shouldDirty: true, shouldTouch: true, shouldValidate: true });
        setValue("apellidos", result.apellidos, { shouldDirty: true, shouldTouch: true, shouldValidate: true });
        setValue("nombres", result.nombres, { shouldDirty: true, shouldTouch: true, shouldValidate: true });
        await trigger(["numeroDocumento", "nombres", "apellidos"]);
        toast.success("Datos del documento cargados");
      }
    } catch (e) {
      // El error ya es manejado por el hook
    }
  }

  return (
    <div className="space-y-2 col-span-12 sm:col-span-8">
      <Label
        htmlFor="numeroDocumento"
        className={cn("text-sm font-medium")}
      >
        Número de Documento <span className="text-destructive ml-1">*</span>
      </Label>

      <div className="flex items-stretch gap-2">
        <div className="flex-1">
          <Controller
            name="numeroDocumento"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                id="numeroDocumento"
                type="text"
                inputMode={inputMode}
                autoComplete="off"
                placeholder={placeholder}
                maxLength={maxLen}
                className={cn(
                  error && "border-destructive ring-1 ring-destructive",
                )}
                onChange={(e) => {
                  const filtered =
                    tipoDocumento === "PAS"
                      ? e.target.value
                          .replace(/[^a-zA-Z0-9]/g, "")
                          .toUpperCase()
                          .slice(0, maxLen)
                      : stripNonDigits(e.target.value).slice(0, maxLen);
                  field.onChange({ target: { value: filtered } });
                }}
              />
            )}
          />
        </div>
        {tipoDocumento === "DNI" && (
          <Button
            type="button"
            variant="default"
            size="icon"
            disabled={!canLookup || documentoLookup.isPending}
            onClick={handleLookup}
            aria-label="Buscar nombres por DNI"
            className="shrink-0 h-10 w-10 bg-primary hover:bg-primary/90 shadow"
          >
            {documentoLookup.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Search className="size-4" />
            )}
          </Button>
        )}
      </div>

      {error && (
        <p className="text-sm text-destructive font-medium">{error}</p>
      )}
    </div>
  );
}
