"use client";

import { CalendarClock } from "lucide-react";
import { type UseFormReturn, useController } from "react-hook-form";
import { z } from "zod";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import { useActualizarEncuentro } from "../hooks/useCompetencias";
import type { EncuentroActualizar } from "../schemas/competencia.schema";
import type { Encuentro } from "../types/competencia.types";
import {
  instanteLocalAIso,
  isoALocal,
} from "../utils/competencias.fecha.utils";

/**
 * The form of the schedule.
 *
 * The operator types the LOCAL time of the edition and the command carries
 * the instant with the offset of the edition: the schedule never shifts with
 * the timezone of the browser.
 */
const formularioProgramacion = z
  .object({
    inicio_programado: z.string().min(1, "Indica la hora de inicio"),
    fin_programado: z.string().min(1, "Indica la hora de fin"),
    motivo: z
      .string()
      .min(5, "El motivo necesita al menos 5 caracteres")
      .max(500, "El motivo es demasiado largo"),
  })
  .refine(
    (valores) =>
      instanteLocalAIso(valores.inicio_programado) !==
      instanteLocalAIso(valores.fin_programado),
    {
      message: "El fin no puede ser antes del inicio",
      path: ["fin_programado"],
    },
  );

type FormularioProgramacion = z.infer<typeof formularioProgramacion>;

/**
 * The command of the schedule.
 *
 * It is a PURE mapping: the local time that the operator typed becomes the
 * instant of the edition, and the version that the panel is drawing travels
 * with it.
 */
export function aPayloadProgramacion(
  datos: FormularioProgramacion,
  version: number,
): EncuentroActualizar {
  return {
    inicio_programado: instanteLocalAIso(datos.inicio_programado),
    fin_programado: instanteLocalAIso(datos.fin_programado),
    motivo: datos.motivo,
    expected_version: version,
  };
}

export interface DialogoProgramacionEncuentroProps {
  /** The encounter that is being scheduled. */
  encuentro: Encuentro;
  /** Whether the dialog is open. */
  open: boolean;
  /** The action that opens and closes the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The failure of the command, when it fails. */
  onError?: (error: unknown) => void;
}

/**
 * The dialog of the schedule of an encounter.
 *
 * It is the ONLY route that publishes a schedule: the `PATCH` of the
 * encounter. The backend rejects a slot that overlaps another match of the
 * same team (`RN-K03`) and nothing is written in that case.
 */
export function DialogoProgramacionEncuentro({
  encuentro,
  open,
  onOpenChange,
  onError,
}: DialogoProgramacionEncuentroProps) {
  const actualizar = useActualizarEncuentro();

  const valoresIniciales: FormularioProgramacion = {
    inicio_programado: isoALocal(encuentro.inicio_programado),
    fin_programado: isoALocal(encuentro.fin_programado),
    motivo: "",
  };

  return (
    <AppFormModal<FormularioProgramacion>
      open={open}
      onOpenChange={onOpenChange}
      title="Programar el encuentro"
      eyebrow="Encuentro"
      icon={
        <CalendarClock className="size-5 text-primary" aria-hidden="true" />
      }
      description="Las horas son la hora local del festival (Lima)."
      primaryLabel="Guardar horario"
      primaryLoadingLabel="Guardando..."
      primaryLoading={actualizar.isPending}
      onPrimary={() => undefined}
      schema={formularioProgramacion}
      initialData={valoresIniciales}
      onSubmit={async (data) => {
        try {
          await actualizar.mutateAsync({
            competenciaId: encuentro.competencia_id,
            encuentroId: encuentro.id,
            datos: aPayloadProgramacion(data, encuentro.version),
          });
        } catch (error) {
          onError?.(error);
          throw error;
        }
      }}
    >
      {({ methods }) => <CamposProgramacion methods={methods} />}
    </AppFormModal>
  );
}

/** The fields of the schedule. */
function CamposProgramacion({
  methods,
}: {
  methods: UseFormReturn<FormularioProgramacion>;
}) {
  const {
    register,
    formState: { errors },
  } = methods;

  const { field: inicio } = useController({
    control: methods.control,
    name: "inicio_programado",
  });

  return (
    <FormGrid>
      <FormField
        id="programacion-inicio"
        label="Inicio"
        required
        icon={CalendarClock}
        span={6}
        error={errors.inicio_programado?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...inicio}
            type="datetime-local"
            value={inicio.value ?? ""}
            onChange={inicio.onChange}
            onBlur={inicio.onBlur}
          />
        )}
      </FormField>

      <FormField
        id="programacion-fin"
        label="Fin"
        required
        icon={CalendarClock}
        span={6}
        error={errors.fin_programado?.message}
      >
        {(control) => (
          <Input
            {...control}
            {...register("fin_programado")}
            type="datetime-local"
          />
        )}
      </FormField>

      <FormField
        id="programacion-motivo"
        label="Motivo"
        required
        icon={CalendarClock}
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
