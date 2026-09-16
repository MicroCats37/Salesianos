"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { handleApiError } from "@/errors/error-handler";
import { notify } from "@/errors/toast-adapter";
import type { AdminInscripcionListItem } from "../hooks/useAllInscripciones";
import { useUpdateInscripcionStatus } from "../hooks/useUpdateInscripcionStatus";

type Status = "en_revision" | "validada" | "observada" | "rechazada";

export function StatusChangeDialog({
  inscripcion,
  onClose,
}: {
  inscripcion: AdminInscripcionListItem;
  onClose: () => void;
}) {
  const [status, setStatus] = useState<Status>("en_revision");
  const [observacion, setObservacion] = useState("");
  const updateMut = useUpdateInscripcionStatus();

  const onSubmit = async () => {
    try {
      await updateMut.mutateAsync({
        inscripcionId: inscripcion.inscripcion.id,
        status,
        observacion: status === "observada" ? observacion : undefined,
      });
      notify.success("Estado actualizado");
      onClose();
    } catch (error) {
      handleApiError(error);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cambiar estado</DialogTitle>
          <DialogDescription>
            {inscripcion.userNombre} {inscripcion.userApellido} —{" "}
            {inscripcion.userDni}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="status">Nuevo estado</Label>
            <Select
              value={status}
              onValueChange={(v) => setStatus(v as Status)}
            >
              <SelectTrigger id="status">
                <SelectValue placeholder="Selecciona un estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en_revision">En revisión</SelectItem>
                <SelectItem value="validada">Validada</SelectItem>
                <SelectItem value="observada">Observada</SelectItem>
                <SelectItem value="rechazada">Rechazada</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {status === "observada" && (
            <div className="space-y-2">
              <Label htmlFor="observacion">Observación (requerido)</Label>
              <Textarea
                id="observacion"
                rows={4}
                value={observacion}
                onChange={(e) => setObservacion(e.target.value)}
                placeholder="Describe qué debe corregir el responsable..."
              />
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            onClick={onSubmit}
            disabled={
              updateMut.isPending ||
              (status === "observada" && !observacion.trim())
            }
          >
            {updateMut.isPending ? "Actualizando..." : "Actualizar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
