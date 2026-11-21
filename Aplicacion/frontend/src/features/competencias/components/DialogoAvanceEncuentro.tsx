"use client";

import { ArrowRightCircle } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import {
  useConfirmarAvance,
  usePrevisualizarAvance,
} from "../hooks/useCompetencias";
import type { Encuentro, VistaPreviaAvance } from "../types/competencia.types";
import { VistaPreviaAvancePanel } from "./VistaPreviaAvancePanel";

/** The minimum length of the audited reason. */
const MINIMO_MOTIVO = 5;

export interface DialogoAvanceEncuentroProps {
  /** The encounter whose winner advances. */
  encuentro: Encuentro;
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/**
 * The dialog of the advance of the winner.
 *
 * It has TWO steps and it is NOT the form modal of the area: the first step
 * is a SIMULATION (`POST …/avance/preview`, which NEVER writes) and the
 * second one is the confirmation (`POST …/avance`). A modal that closes on
 * submit cannot show a simulation before the write, so this one owns its
 * two steps (`QA-K04`).
 */
export function DialogoAvanceEncuentro({
  encuentro,
  open,
  onOpenChange,
  onError,
}: DialogoAvanceEncuentroProps) {
  const previsualizar = usePrevisualizarAvance();
  const confirmar = useConfirmarAvance();

  const [vistaPrevia, setVistaPrevia] = useState<VistaPreviaAvance | null>(
    null,
  );
  const [motivo, setMotivo] = useState("");
  const [errorMotivo, setErrorMotivo] = useState<string | null>(null);

  /**
   * The simulation of the advance.
   *
   * It NEVER writes (`QA-K04`), so it is asked for EXPLICITLY and it does
   * not dirty any cache.
   */
  const verAvance = async () => {
    try {
      const resultado = await previsualizar.mutateAsync({
        competenciaId: encuentro.competencia_id,
        encuentroId: encuentro.id,
      });
      setVistaPrevia(resultado);
    } catch (error) {
      onError?.(error);
    }
  };

  const confirmarAvance = async () => {
    if (motivo.trim().length < MINIMO_MOTIVO) {
      setErrorMotivo("El motivo necesita al menos 5 caracteres");
      return;
    }
    setErrorMotivo(null);

    try {
      await confirmar.mutateAsync({
        competenciaId: encuentro.competencia_id,
        encuentroId: encuentro.id,
        datos: {
          motivo: motivo.trim(),
          expected_version: encuentro.version,
        },
      });
      onOpenChange(false);
    } catch (error) {
      onError?.(error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Confirmar el avance</DialogTitle>
          <DialogDescription>
            El ganador ocupa el slot del destino. Esta simulación no escribe
            nada: el avance se confirma después.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {previsualizar.isPending ? (
            <p className="text-sm text-muted-foreground">
              Calculando a dónde llegaría el ganador...
            </p>
          ) : null}

          {vistaPrevia ? (
            <VistaPreviaAvancePanel vistaPrevia={vistaPrevia} />
          ) : null}

          {!vistaPrevia && !previsualizar.isPending ? (
            <Button
              type="button"
              variant="secondary"
              className="min-h-11 w-fit"
              onClick={() => void verAvance()}
            >
              Ver a dónde llegaría el ganador
            </Button>
          ) : null}

          <div className="flex flex-col gap-1">
            <label
              htmlFor="avance-motivo"
              className="text-sm font-medium text-foreground"
            >
              Motivo
            </label>
            <Input
              id="avance-motivo"
              value={motivo}
              onChange={(evento) => setMotivo(evento.target.value)}
              maxLength={500}
              aria-invalid={errorMotivo ? true : undefined}
              aria-describedby={errorMotivo ? "avance-motivo-error" : undefined}
            />
            {errorMotivo ? (
              <p id="avance-motivo-error" className="text-sm text-destructive">
                {errorMotivo}
              </p>
            ) : null}
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            className="min-h-11"
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            className="min-h-11"
            disabled={
              confirmar.isPending ||
              previsualizar.isPending ||
              !vistaPrevia?.puede_confirmar
            }
            onClick={() => void confirmarAvance()}
          >
            <ArrowRightCircle className="size-4" aria-hidden="true" />
            {confirmar.isPending ? "Confirmando..." : "Confirmar avance"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
