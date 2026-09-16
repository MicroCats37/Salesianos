"use client";

import { Building2, Loader2, Plus } from "lucide-react";
import { useCallback, useState } from "react";
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
import { useIncorporarArea } from "@/features/asignaciones/hooks";
import type { IncorporarAreaData } from "@/features/asignaciones/schemas/asignacion.schema";
import { useAreas } from "@/features/tramites/hooks/useAreas";
import type { TipoParticipacion } from "@/shared/constants/tramite.tokens";

interface IncorporarAreaModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  solicitudId: string;
  /** IDs of areas already assigned to this Solicitud — will be filtered out */
  assignedAreaIds?: string[];
  onSuccess?: () => void;
}

export function IncorporarAreaModal({
  open,
  onOpenChange,
  solicitudId,
  assignedAreaIds = [],
  onSuccess,
}: IncorporarAreaModalProps) {
  const incorporarMutation = useIncorporarArea(solicitudId);
  const { areas, isLoading: areasLoading } = useAreas();

  const [areaId, setAreaId] = useState<string>("");
  const [tipoParticipacion, setTipoParticipacion] =
    useState<TipoParticipacion>("PRINCIPAL");
  const [observacion, setObservacion] = useState<string>("");

  const availableAreas = areas.filter(
    (area) => !assignedAreaIds.includes(area.id),
  );

  const resetForm = useCallback(() => {
    setAreaId("");
    setTipoParticipacion("PRINCIPAL");
    setObservacion("");
  }, []);

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
    if (!areaId) {
      notify.error("Selecciona un área");
      return;
    }

    const payload: IncorporarAreaData = {
      area_id: areaId,
      tipo_participacion: tipoParticipacion,
      observacion: observacion.trim() || null,
    };

    try {
      await incorporarMutation.mutateAsync(payload);
      notify.success("Área incorporada correctamente");
      resetForm();
      onSuccess?.();
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  }, [
    areaId,
    tipoParticipacion,
    observacion,
    incorporarMutation,
    resetForm,
    onSuccess,
    onOpenChange,
  ]);

  return (
    <GenericModal open={open} onOpenChange={handleClose} preventClose={false}>
      <GenericModal.Content size="md">
        <GenericModal.Header
          title=""
          className="bg-primary/[0.03] border-b border-border px-6 py-5"
        >
          <div className="flex items-center gap-3 w-full">
            <div className="p-2 bg-primary/10 rounded-xl border border-primary/20 shadow-sm shrink-0">
              <Plus className="h-5 w-5 text-primary" />
            </div>
            <div className="flex flex-col gap-0.5 min-w-0 flex-1">
              <span className="hidden sm:block text-[10px] font-bold uppercase tracking-widest text-primary leading-none">
                Incorporar Área
              </span>
              <h2 className="text-2xl font-black tracking-tight text-foreground leading-tight">
                Incorporar área a la solicitud
              </h2>
              <p className="hidden sm:block text-sm text-muted-foreground leading-relaxed">
                Agrega una nueva área de participación a esta solicitud
              </p>
            </div>
            <div className="w-9 shrink-0" aria-hidden="true" />
          </div>
        </GenericModal.Header>

        <GenericModal.Body className="space-y-5">
          {/* Area selector */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              Área
            </label>
            {areasLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Cargando áreas...
              </div>
            ) : availableAreas.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">
                No hay áreas disponibles para agregar. Todas las áreas activas
                ya están asignadas a esta solicitud.
              </p>
            ) : (
              <Select value={areaId} onValueChange={setAreaId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Selecciona un área" />
                </SelectTrigger>
                <SelectContent>
                  {availableAreas.map((area) => (
                    <SelectItem key={area.id} value={area.id}>
                      {area.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Tipo participación */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Tipo de participación
            </label>
            <Select
              value={tipoParticipacion}
              onValueChange={(v) =>
                setTipoParticipacion(v as TipoParticipacion)
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PRINCIPAL">Principal</SelectItem>
                <SelectItem value="ADJUNTA">Adjunta</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Observación */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">
              Observación{" "}
              <span className="text-xs font-normal text-muted-foreground">
                (opcional)
              </span>
            </label>
            <Textarea
              value={observacion}
              onChange={(e) => setObservacion(e.target.value)}
              placeholder="Motivo o razón para incorporar esta área..."
              rows={3}
            />
          </div>
        </GenericModal.Body>

        <GenericModal.Footer className="px-6 py-4 bg-muted/30 border-t border-border">
          <div className="flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={incorporarMutation.isPending}
              className="h-10 rounded-xl font-semibold"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={
                incorporarMutation.isPending ||
                !areaId ||
                availableAreas.length === 0
              }
              className="h-10 rounded-xl font-bold gap-1.5"
            >
              {incorporarMutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              <Plus className="h-4 w-4" />
              Incorporar área
            </Button>
          </div>
        </GenericModal.Footer>

        <GenericModal.CloseX />
      </GenericModal.Content>
    </GenericModal>
  );
}
