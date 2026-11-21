"use client";

import { PlayCircle } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { z } from "zod";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useActualizarEncuentro } from "../hooks/useCompetencias";
import type { Encuentro } from "../types/competencia.types";

/**
 * The form of a change of state.
 *
 * A state change is an audited operation: the motive is OBLIGATORIOUS and
 * the backend rejects the command without it (`MOTIVO_REQUERIDO`).
 */
const formularioEstado = z.object({
  motivo: z
    .string()
    .min(5, "El motivo necesita al menos 5 caracteres")
    .max(500, "El motivo es demasiado largo"),
});

type FormularioEstado = z.infer<typeof formularioEstado>;

export interface DialogoEstadoEncuentroProps {
  /** The encounter that is changing its state. */
  encuentro: Encuentro;
  /** The state the server will move the encounter to. */
  estado: "PROGRAMADO" | "EN_CURSO" | "CANCELADO" | "BORRADOR";
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/** The wording of each state, for the reader of the dialog. */
const TITULOS: Record<DialogoEstadoEncuentroProps["estado"], string> = {
  PROGRAMADO: "Programar el encuentro",
  EN_CURSO: "Iniciar el encuentro",
  CANCELADO: "Cancelar el encuentro",
  BORRADOR: "Quitar la programación",
};

/**
 * The dialog of a change of state.
 *
 * It is the SAME `PATCH` of the encounter that programs it: only the state
 * changes. The transitions are NOT recreated in the browser: the server
 * decides if the change is legal and the browser only offers the states
 * that the server advertises in `acciones`.
 */
export function DialogoEstadoEncuentro({
  encuentro,
  estado,
  open,
  onOpenChange,
  onError,
}: DialogoEstadoEncuentroProps) {
  const actualizar = useActualizarEncuentro();

  const valoresIniciales: FormularioEstado = { motivo: "" };

  return (
    <AppFormModal<FormularioEstado>
      open={open}
      onOpenChange={onOpenChange}
      title={TITULOS[estado]}
      eyebrow="Encuentro"
      icon={<PlayCircle className="size-5 text-primary" aria-hidden="true" />}
      description="El cambio de estado queda auditado con su motivo."
      primaryLabel="Confirmar"
      primaryLoadingLabel="Guardando..."
      primaryLoading={actualizar.isPending}
      onPrimary={() => undefined}
      schema={formularioEstado}
      initialData={valoresIniciales}
      onSubmit={async (data) => {
        try {
          await actualizar.mutateAsync({
            competenciaId: encuentro.competencia_id,
            encuentroId: encuentro.id,
            datos: {
              estado,
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
      {({ methods }) => <CamposEstado methods={methods} />}
    </AppFormModal>
  );
}

/** The fields of the change of state. */
function CamposEstado({
  methods,
}: {
  methods: UseFormReturn<FormularioEstado>;
}) {
  const {
    register,
    formState: { errors },
  } = methods;

  return (
    <FormGrid>
      <FormField
        id="estado-motivo"
        label="Motivo"
        required
        icon={PlayCircle}
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
