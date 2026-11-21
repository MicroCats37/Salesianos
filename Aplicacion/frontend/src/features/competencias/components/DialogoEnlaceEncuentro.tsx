"use client";

import { Link2 } from "lucide-react";
import { type UseFormReturn, useController } from "react-hook-form";
import { z } from "zod";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useActualizarEncuentro } from "../hooks/useCompetencias";
import type { Encuentro } from "../types/competencia.types";

/**
 * The form of the link with the next round.
 *
 * The destination and its slot TRAVEL TOGETHER: the backend rejects the
 * command when only one of the two arrives (`ENLACE_INVALIDO`).
 */
const formularioEnlace = z.object({
  siguiente_encuentro_id: z.string().min(1, "Elige el encuentro destino"),
  slot_destino: z.enum(["PARTICIPANTE_1", "PARTICIPANTE_2"], {
    message: "Elige el slot que recibe al ganador",
  }),
  motivo: z
    .string()
    .min(5, "El motivo necesita al menos 5 caracteres")
    .max(500, "El motivo es demasiado largo"),
});

type FormularioEnlace = z.infer<typeof formularioEnlace>;

export interface DialogoEnlaceEncuentroProps {
  /** The encounter that is being linked. */
  encuentro: Encuentro;
  /** The encounters that can receive the winner. */
  destinos: readonly Encuentro[];
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/**
 * The dialog of the link of an encounter with its destination.
 *
 * The link is what MAKES the advance possible: the server only advertises
 * the action `avanzar` when the encounter already has a destination.
 */
export function DialogoEnlaceEncuentro({
  encuentro,
  destinos,
  open,
  onOpenChange,
  onError,
}: DialogoEnlaceEncuentroProps) {
  const actualizar = useActualizarEncuentro();

  const valoresIniciales: FormularioEnlace = {
    siguiente_encuentro_id: "",
    slot_destino: "PARTICIPANTE_1",
    motivo: "",
  };

  return (
    <AppFormModal<FormularioEnlace>
      open={open}
      onOpenChange={onOpenChange}
      title="Enlazar con el destino"
      eyebrow="Encuentro"
      icon={<Link2 className="size-5 text-primary" aria-hidden="true" />}
      description="El ganador de este encuentro viajará al slot que elijas."
      primaryLabel="Enlazar"
      primaryLoadingLabel="Guardando..."
      primaryLoading={actualizar.isPending}
      primaryDisabled={destinos.length === 0}
      onPrimary={() => undefined}
      schema={formularioEnlace}
      initialData={valoresIniciales}
      onSubmit={async (data) => {
        try {
          await actualizar.mutateAsync({
            competenciaId: encuentro.competencia_id,
            encuentroId: encuentro.id,
            datos: {
              siguiente_encuentro_id: data.siguiente_encuentro_id,
              slot_destino: data.slot_destino,
              motivo: data.motivo,
              expected_version: encuentro.version,
            },
          });
        } catch (error) {
          onError?.(error);
          throw error;
        }
      }}
    >
      {({ methods }) => <CamposEnlace methods={methods} destinos={destinos} />}
    </AppFormModal>
  );
}

/** The fields of the link. */
function CamposEnlace({
  methods,
  destinos,
}: {
  methods: UseFormReturn<FormularioEnlace>;
  destinos: readonly Encuentro[];
}) {
  const {
    control,
    register,
    formState: { errors },
  } = methods;

  const { field: destino } = useController({
    control,
    name: "siguiente_encuentro_id",
  });

  const { field: slot } = useController({
    control,
    name: "slot_destino",
  });

  return (
    <FormGrid>
      <FormField
        id="enlace-destino"
        label="Encuentro destino"
        required
        icon={Link2}
        span={12}
        helper="Sólo las rondas posteriores pueden recibir al ganador."
        error={errors.siguiente_encuentro_id?.message}
      >
        {(control) => (
          <Select
            value={destino.value ?? ""}
            onValueChange={destino.onChange}
            disabled={destinos.length === 0}
          >
            <SelectTrigger
              {...control}
              onBlur={destino.onBlur}
              className="w-full"
            >
              <SelectValue placeholder="Elige el destino" />
            </SelectTrigger>
            <SelectContent>
              {destinos.map((candidato) => (
                <SelectItem key={candidato.id} value={candidato.id}>
                  {candidato.ronda_etiqueta} · encuentro {candidato.orden}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </FormField>

      <FormField
        id="enlace-slot"
        label="Slot que recibe al ganador"
        required
        icon={Link2}
        span={12}
        error={errors.slot_destino?.message}
      >
        {(control) => (
          <RadioGroup
            value={slot.value ?? "PARTICIPANTE_1"}
            onValueChange={slot.onChange}
            aria-label="Slot que recibe al ganador"
          >
            {(["PARTICIPANTE_1", "PARTICIPANTE_2"] as const).map((valor) => {
              const idRadio = `${control.id}-${valor}`;
              return (
                <div key={valor} className="flex items-center gap-2">
                  <RadioGroupItem id={idRadio} value={valor} />
                  <label
                    htmlFor={idRadio}
                    className="text-sm font-medium text-foreground"
                  >
                    {valor === "PARTICIPANTE_1"
                      ? "Participante 1"
                      : "Participante 2"}
                  </label>
                </div>
              );
            })}
          </RadioGroup>
        )}
      </FormField>

      <FormField
        id="enlace-motivo"
        label="Motivo"
        required
        icon={Link2}
        span={12}
        helper="Queda auditado: entre 5 y 500 caracteres."
        error={errors.motivo?.message}
      >
        {(control) => (
          <Textarea
            {...control}
            {...register("motivo")}
            rows={2}
            maxLength={500}
          />
        )}
      </FormField>
    </FormGrid>
  );
}
