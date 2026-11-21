"use client";

import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  useCorregirEncuentro,
  usePrevisualizarCorreccion,
} from "../hooks/useCompetencias";
import type {
  Encuentro,
  VistaPreviaCorreccion,
} from "../types/competencia.types";
import { VistaPreviaCorreccionPanel } from "./VistaPreviaCorreccionPanel";

/** The minimum length of the audited reason. */
const MINIMO_MOTIVO = 5;

export interface DialogoCorreccionEncuentroProps {
  /** The encounter whose result is being corrected. */
  encuentro: Encuentro;
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/**
 * The dialog of the correction of the result.
 *
 * It has TWO steps and it is NOT the form modal of the area: the first step
 * is the IMPACT (`POST …/correccion/preview`, which NEVER writes) and the
 * second one is the application (`POST …/correccion`), which needs the
 * reason, the explicit authorisation and the acceptance of the impact
 * (`QA-K03`).
 *
 * **The new winner is CHOSEN, never derived** from the old result.
 */
export function DialogoCorreccionEncuentro({
  encuentro,
  open,
  onOpenChange,
  onError,
}: DialogoCorreccionEncuentroProps) {
  const previsualizar = usePrevisualizarCorreccion();
  const corregir = useCorregirEncuentro();

  const [ganadorId, setGanadorId] = useState("");
  const [motivo, setMotivo] = useState("");
  const [override, setOverride] = useState(false);
  const [aceptaImpacto, setAceptaImpacto] = useState(false);
  const [vistaPrevia, setVistaPrevia] = useState<VistaPreviaCorreccion | null>(
    null,
  );
  const [errorMotivo, setErrorMotivo] = useState<string | null>(null);

  const opciones = encuentro.participantes
    .filter((participante) => participante.competencia_equipo_id !== null)
    .map((participante) => ({
      valor: participante.competencia_equipo_id ?? "",
      etiqueta: participante.equipo_nombre ?? "Equipo por definir",
    }));

  const verImpacto = async () => {
    if (!ganadorId) return;
    try {
      const resultado = await previsualizar.mutateAsync({
        competenciaId: encuentro.competencia_id,
        encuentroId: encuentro.id,
        datos: { ganador_id: ganadorId },
      });
      setVistaPrevia(resultado);
    } catch (error) {
      onError?.(error);
    }
  };

  const aplicar = async () => {
    if (motivo.trim().length < MINIMO_MOTIVO) {
      setErrorMotivo("El motivo necesita al menos 5 caracteres");
      return;
    }
    setErrorMotivo(null);

    try {
      await corregir.mutateAsync({
        competenciaId: encuentro.competencia_id,
        encuentroId: encuentro.id,
        datos: {
          ganador_id: ganadorId,
          motivo: motivo.trim(),
          override,
          acepta_impacto: aceptaImpacto,
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
          <DialogTitle>Corregir el resultado</DialogTitle>
          <DialogDescription>
            Primero mira el impacto y después confirma. La vista previa no
            escribe nada.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm font-medium text-foreground">
              Nuevo equipo ganador
            </legend>
            <RadioGroup
              value={ganadorId}
              onValueChange={(valor) => {
                setGanadorId(valor);
                setVistaPrevia(null);
              }}
              aria-label="Nuevo equipo ganador"
            >
              {opciones.map((opcion) => {
                const idRadio = `correccion-ganador-${opcion.valor}`;
                return (
                  <div key={opcion.valor} className="flex items-center gap-2">
                    <RadioGroupItem id={idRadio} value={opcion.valor} />
                    <label
                      htmlFor={idRadio}
                      className="text-sm font-medium text-foreground"
                    >
                      {opcion.etiqueta}
                    </label>
                  </div>
                );
              })}
            </RadioGroup>
          </fieldset>

          {previsualizar.isPending ? (
            <p className="text-sm text-muted-foreground">
              Calculando el impacto de la corrección...
            </p>
          ) : null}

          {vistaPrevia ? (
            <VistaPreviaCorreccionPanel vistaPrevia={vistaPrevia} />
          ) : null}

          <div className="flex flex-col gap-1">
            <label
              htmlFor="correccion-motivo"
              className="text-sm font-medium text-foreground"
            >
              Motivo
            </label>
            <Input
              id="correccion-motivo"
              value={motivo}
              onChange={(evento) => setMotivo(evento.target.value)}
              maxLength={500}
              aria-invalid={errorMotivo ? true : undefined}
              aria-describedby={
                errorMotivo ? "correccion-motivo-error" : undefined
              }
            />
            {errorMotivo ? (
              <p
                id="correccion-motivo-error"
                className="text-sm text-destructive"
              >
                {errorMotivo}
              </p>
            ) : null}
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-start gap-2">
              <Checkbox
                id="correccion-override"
                checked={override}
                onCheckedChange={(valor) => setOverride(valor === true)}
              />
              <label
                htmlFor="correccion-override"
                className="text-sm text-foreground"
              >
                Autorizo corregir aunque un descendiente ya haya transcurrido.
              </label>
            </div>
            <div className="flex items-start gap-2">
              <Checkbox
                id="correccion-impacto"
                checked={aceptaImpacto}
                onCheckedChange={(valor) => setAceptaImpacto(valor === true)}
              />
              <label
                htmlFor="correccion-impacto"
                className="text-sm text-foreground"
              >
                Acepto el impacto calculado de la corrección.
              </label>
            </div>
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
          {vistaPrevia ? (
            <Button
              type="button"
              className="min-h-11"
              disabled={corregir.isPending}
              onClick={() => void aplicar()}
            >
              <ShieldCheck className="size-4" aria-hidden="true" />
              {corregir.isPending ? "Corrigiendo..." : "Aplicar corrección"}
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              className="min-h-11"
              disabled={!ganadorId || previsualizar.isPending}
              onClick={() => void verImpacto()}
            >
              {previsualizar.isPending ? "Calculando..." : "Ver el impacto"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
