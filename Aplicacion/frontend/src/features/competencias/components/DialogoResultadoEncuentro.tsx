"use client";

import { Trophy } from "lucide-react";
import { type UseFormReturn, useController } from "react-hook-form";
import { z } from "zod";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useRegistrarResultado } from "../hooks/useCompetencias";
import type { ResultadoRegistrar } from "../schemas/competencia.schema";
import type { Encuentro } from "../types/competencia.types";

/**
 * The form of the result.
 *
 * It is NOT the wire: the form works with the TEXTS that the operator types
 * and the COMMAND carries the numbers and the version. The exact mirror of
 * the wire (`resultadoRegistrarSchema`) is applied by the client, on the
 * payload that leaves.
 *
 * **The winner is CHOSEN, never derived.** The score is informative: the
 * radio group asks who won and the browser never compares two numbers
 * (`GOV-02-RB-05c`).
 */
const puntajeOpcional = z.union([
  z.literal(""),
  z.string().regex(/^\d+$/, "El puntaje es un número entero no negativo"),
]);

const formularioResultado = z.object({
  ganador_id: z.string().min(1, "Elige el equipo ganador"),
  puntaje_1: puntajeOpcional,
  puntaje_2: puntajeOpcional,
  marcador_detalle: z.string().max(500).optional(),
  motivo: z
    .string()
    .min(5, "El motivo necesita al menos 5 caracteres")
    .max(500, "El motivo es demasiado largo"),
});

type FormularioResultado = z.infer<typeof formularioResultado>;

/**
 * The command of the result.
 *
 * It is a PURE mapping: the form talks in texts and the command travels in
 * the wire. The `expected_version` is the version of the encounter that the
 * panel is DRAWING: the browser never decides whether a write is current.
 *
 * **The winner travels as it was CHOSEN.** The score never decides it: a
 * 9-4 with the second team as the winner travels with the second team
 * (`GOV-02-RB-05c`).
 */
export function aPayloadResultado(
  datos: FormularioResultado,
  version: number,
): ResultadoRegistrar {
  return {
    ganador_id: datos.ganador_id,
    puntaje_1: datos.puntaje_1 ? Number(datos.puntaje_1) : null,
    puntaje_2: datos.puntaje_2 ? Number(datos.puntaje_2) : null,
    marcador_detalle: datos.marcador_detalle || null,
    motivo: datos.motivo,
    expected_version: version,
  };
}

const valoresIniciales: FormularioResultado = {
  ganador_id: "",
  puntaje_1: "",
  puntaje_2: "",
  marcador_detalle: "",
  motivo: "",
};

export interface DialogoResultadoEncuentroProps {
  /** The encounter that is being finished. */
  encuentro: Encuentro;
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/**
 * The dialog of the result of an encounter.
 *
 * The winner travels as the PARTICIPATION that occupies a slot (not as the
 * team): that is what the backend validates.
 */
export function DialogoResultadoEncuentro({
  encuentro,
  open,
  onOpenChange,
  onError,
}: DialogoResultadoEncuentroProps) {
  const registrar = useRegistrarResultado();

  const opciones = encuentro.participantes
    .filter((participante) => participante.competencia_equipo_id !== null)
    .map((participante) => ({
      valor: participante.competencia_equipo_id ?? "",
      etiqueta: participante.equipo_nombre ?? "Equipo por definir",
    }));

  return (
    <AppFormModal<FormularioResultado>
      open={open}
      onOpenChange={onOpenChange}
      title="Registrar el resultado"
      eyebrow="Encuentro"
      icon={<Trophy className="size-5 text-primary" aria-hidden="true" />}
      description="El ganador lo declaras tú: el marcador es sólo información."
      primaryLabel="Registrar resultado"
      primaryLoadingLabel="Registrando..."
      primaryLoading={registrar.isPending}
      primaryDisabled={opciones.length === 0}
      onPrimary={() => undefined}
      schema={formularioResultado}
      initialData={valoresIniciales}
      onSubmit={async (data) => {
        try {
          await registrar.mutateAsync({
            competenciaId: encuentro.competencia_id,
            encuentroId: encuentro.id,
            datos: aPayloadResultado(data, encuentro.version),
          });
        } catch (error) {
          onError?.(error);
          throw error;
        }
      }}
    >
      {({ methods }) => (
        <CamposResultado methods={methods} opciones={opciones} />
      )}
    </AppFormModal>
  );
}

/**
 * The fields of the result.
 *
 * The winner is a CONTROLLED field: its value is read with `useController`
 * scoped to its own field, never with a global `watch()`.
 */
function CamposResultado({
  methods,
  opciones,
}: {
  methods: UseFormReturn<FormularioResultado>;
  opciones: readonly { valor: string; etiqueta: string }[];
}) {
  const {
    control,
    register,
    formState: { errors },
  } = methods;

  const { field: ganador } = useController({
    control,
    name: "ganador_id",
  });

  return (
    <FormGrid>
      <FormField
        id="resultado-ganador"
        label="Equipo ganador"
        required
        icon={Trophy}
        span={12}
        error={errors.ganador_id?.message}
      >
        {(control) => (
          <RadioGroup
            value={ganador.value ?? ""}
            onValueChange={ganador.onChange}
            aria-label="Equipo ganador"
          >
            {opciones.map((opcion) => {
              const idRadio = `${control.id}-${opcion.valor}`;
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
        )}
      </FormField>

      <FormField
        id="resultado-puntaje-1"
        label="Puntaje del participante 1"
        icon={Trophy}
        span={6}
        error={errors.puntaje_1?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("puntaje_1")}
            inputMode="numeric"
            placeholder="Sin puntaje"
          />
        )}
      </FormField>

      <FormField
        id="resultado-puntaje-2"
        label="Puntaje del participante 2"
        icon={Trophy}
        span={6}
        error={errors.puntaje_2?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("puntaje_2")}
            inputMode="numeric"
            placeholder="Sin puntaje"
          />
        )}
      </FormField>

      <FormField
        id="resultado-detalle"
        label="Detalle del marcador"
        icon={Trophy}
        span={12}
        helper="Opcional: un texto con el detalle de los sets."
        error={errors.marcador_detalle?.message}
      >
        {(control) => (
          <Textarea
            {...control}
            {...register("marcador_detalle")}
            rows={2}
            maxLength={500}
          />
        )}
      </FormField>

      <FormField
        id="resultado-motivo"
        label="Motivo"
        required
        icon={Trophy}
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
