"use client";

import {
  AlertTriangle,
  ArrowLeftRight,
  Loader2,
  PlayCircle,
} from "lucide-react";
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
import type {
  CambiarParticipacionData,
  MarcarAsignacionErroneaData,
} from "@/features/asignaciones/schemas/asignacion.schema";
import type { TipoParticipacion } from "@/shared/constants/tramite.tokens";
import type { PeriodoOperation } from "./PeriodoOperacionesMenu";

type OperationConfig = {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBgClass: string;
  submitLabel: string;
};

const OPERATION_CONFIGS: Record<PeriodoOperation, OperationConfig> = {
  "iniciar-gestion": {
    title: "Iniciar gestión",
    description: "Comenzar la atención de este período",
    icon: PlayCircle,
    iconBgClass: "bg-green-500/10 border border-green-500/20",
    submitLabel: "Iniciar",
  },
  "marcar-erronea": {
    title: "Marcar como errónea",
    description: "Indicar que la asignación fue incorrecta",
    icon: AlertTriangle,
    iconBgClass: "bg-amber-500/10 border border-amber-500/20",
    submitLabel: "Marcar",
  },
  "cambiar-participacion": {
    title: "Cambiar tipo de participación",
    description:
      "Cerrará el ciclo actual y abrirá uno nuevo con el tipo seleccionado",
    icon: ArrowLeftRight,
    iconBgClass: "bg-blue-500/10 border border-blue-500/20",
    submitLabel: "Cambiar",
  },
};

interface PeriodoOperacionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  periodoId: string;
  operation: PeriodoOperation | null;
  onSuccess?: () => void;
  // Mutations
  iniciarGestion: {
    mutateAsync: (periodoId: string) => Promise<unknown>;
    isPending: boolean;
  };
  marcarErronea: {
    mutateAsync: (payload: {
      periodoId: string;
      data: MarcarAsignacionErroneaData;
    }) => Promise<unknown>;
    isPending: boolean;
  };
  cambiarParticipacion: {
    mutateAsync: (payload: {
      periodoId: string;
      data: CambiarParticipacionData;
    }) => Promise<unknown>;
    isPending: boolean;
  };
}

export function PeriodoOperacionModal({
  open,
  onOpenChange,
  periodoId,
  operation,
  onSuccess,
  iniciarGestion,
  marcarErronea,
  cambiarParticipacion,
}: PeriodoOperacionModalProps) {
  const [motivoErronea, setMotivoErronea] = useState("");
  const [tipoParticipacion, setTipoParticipacion] =
    useState<TipoParticipacion>("PRINCIPAL");
  const [motivoParticipacion, setMotivoParticipacion] = useState("");

  const resetForm = useCallback(() => {
    setMotivoErronea("");
    setTipoParticipacion("PRINCIPAL");
    setMotivoParticipacion("");
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

  const isMutationPending =
    iniciarGestion.isPending ||
    marcarErronea.isPending ||
    cambiarParticipacion.isPending;

  const getOperationIcon = () => {
    if (!operation) return null;
    const config = OPERATION_CONFIGS[operation];
    const Icon = config.icon;
    return (
      <div className={`p-2 rounded-xl border shadow-sm ${config.iconBgClass}`}>
        <Icon className="h-5 w-5 text-foreground" />
      </div>
    );
  };

  const handleSubmit = useCallback(async () => {
    if (!operation || !periodoId) return;

    try {
      switch (operation) {
        case "iniciar-gestion":
          await iniciarGestion.mutateAsync(periodoId);
          notify.success("Gestión iniciada correctamente");
          break;
        case "marcar-erronea":
          if (!motivoErronea.trim()) {
            notify.error("El motivo es requerido");
            return;
          }
          await marcarErronea.mutateAsync({
            periodoId,
            data: { motivo: motivoErronea.trim() },
          });
          notify.success("Asignación marcada como errónea");
          break;
        case "cambiar-participacion":
          await cambiarParticipacion.mutateAsync({
            periodoId,
            data: {
              tipo_participacion: tipoParticipacion,
              ...(motivoParticipacion.trim() && {
                motivo: motivoParticipacion.trim(),
              }),
            },
          });
          notify.success("Ciclo cerrado. Nuevo período abierto.");
          break;
      }
      resetForm();
      onSuccess?.();
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  }, [
    operation,
    periodoId,
    motivoErronea,
    tipoParticipacion,
    motivoParticipacion,
    iniciarGestion,
    marcarErronea,
    cambiarParticipacion,
    resetForm,
    onSuccess,
    onOpenChange,
  ]);

  if (!operation) return null;

  const config = OPERATION_CONFIGS[operation];

  return (
    <GenericModal open={open} onOpenChange={handleClose} preventClose={false}>
      <GenericModal.Content size="md">
        <GenericModal.Header className="bg-primary/[0.03] border-b border-border px-6 py-5">
          <div className="flex items-center gap-3 w-full">
            {getOperationIcon()}
            <div className="flex flex-col gap-0.5 min-w-0 flex-1">
              <span className="hidden sm:block text-[10px] font-bold uppercase tracking-widest text-primary leading-none">
                Operaciones
              </span>
              <h2 className="text-2xl font-black tracking-tight text-foreground leading-tight">
                {config.title}
              </h2>
              <p className="hidden sm:block text-sm text-muted-foreground leading-relaxed">
                {config.description}
              </p>
            </div>
            <div className="w-9 shrink-0" aria-hidden="true" />
          </div>
        </GenericModal.Header>

        <GenericModal.Body className="space-y-5">
          {operation === "marcar-erronea" && (
            <div className="space-y-2">
              <label
                htmlFor="motivoErronea"
                className="text-sm font-semibold text-foreground"
              >
                Motivo
              </label>
              <Textarea
                id="motivoErronea"
                value={motivoErronea}
                onChange={(e) => setMotivoErronea(e.target.value)}
                placeholder="Describe por qué la asignación fue errónea..."
                rows={3}
              />
            </div>
          )}

          {operation === "cambiar-participacion" && (
            <>
              <div className="space-y-2">
                <label
                  htmlFor="tipoParticipacion"
                  className="text-sm font-semibold text-foreground"
                >
                  Tipo de participación
                </label>
                <Select
                  value={tipoParticipacion}
                  onValueChange={(v) =>
                    setTipoParticipacion(v as TipoParticipacion)
                  }
                >
                  <SelectTrigger id="tipoParticipacion" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PRINCIPAL">Principal</SelectItem>
                    <SelectItem value="ADJUNTA">Adjunta</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="motivoParticipacion"
                  className="text-sm font-semibold text-foreground"
                >
                  Motivo{" "}
                  <span className="text-muted-foreground font-normal">
                    (opcional)
                  </span>
                </label>
                <Textarea
                  id="motivoParticipacion"
                  value={motivoParticipacion}
                  onChange={(e) => setMotivoParticipacion(e.target.value)}
                  placeholder="Describe el motivo del cambio de participación..."
                  rows={2}
                />
              </div>
            </>
          )}

          {operation === "iniciar-gestion" && (
            <p className="text-sm text-muted-foreground">
              ¿Estás seguro de que deseas iniciar la gestión de este período?
              Esta acción marcará el período como &quot;En gestión&quot;.
            </p>
          )}
        </GenericModal.Body>

        <GenericModal.Footer className="px-6 py-4 bg-muted/30 border-t border-border">
          <div className="flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={isMutationPending}
              className="h-10 rounded-xl font-semibold"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isMutationPending}
              className="h-10 rounded-xl font-bold gap-1.5"
            >
              {isMutationPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              {config.submitLabel}
            </Button>
          </div>
        </GenericModal.Footer>

        <GenericModal.CloseX />
      </GenericModal.Content>
    </GenericModal>
  );
}
