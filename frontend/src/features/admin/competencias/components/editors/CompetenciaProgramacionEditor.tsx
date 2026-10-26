"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import { useProgramarEncuentro, type VariablesProgramacion } from "../../hooks";
import { type Encuentro, EncuentroProgramacionFormSchema } from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editor of the SCHEDULE of an encounter.
 *
 * The schedule is a POSITIVE interval of the day of the competition: the two
 * instants always share the date of the competition and the end is never
 * before the start. The domain rejects the invalid schedule with 422
 * `INVALID_SCHEDULE` and the overlapping one with 409 `EQUIPO_SOLAPADO`.
 */

/** Fields of the schedule. */
const CAMPOS_PROGRAMACION: FormField[] = [
  {
    name: "fecha",
    label: "Fecha del encuentro",
    type: "text",
    required: true,
    placeholder: "2026-10-25",
    helperText: "El horario comparte siempre la fecha de la competencia.",
    containerClassName: "col-span-12 md:col-span-4",
  },
  {
    name: "hora_inicio",
    label: "Hora de inicio",
    type: "text",
    required: true,
    placeholder: "10:00",
    inputMode: "numeric",
    containerClassName: "col-span-12 md:col-span-4",
  },
  {
    name: "hora_fin",
    label: "Hora de fin",
    type: "text",
    required: true,
    placeholder: "10:45",
    inputMode: "numeric",
    containerClassName: "col-span-12 md:col-span-4",
  },
  {
    name: "motivo",
    label: "Motivo del cambio",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText:
      "Cambiar el horario es una decisión auditada: el motivo es obligatorio.",
    containerClassName: "col-span-12",
  },
];

/** The `HH:mm` of an instant of the backend (`null` when it has none). */
function horaDe(instanto: string | null): string {
  if (!instanto) return "";
  const corte = instanto.indexOf("T");
  if (corte < 0) return "";
  return instanto.slice(corte + 1, corte + 6);
}

export interface CompetenciaProgramacionEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter that is being scheduled. */
  encuentro: Encuentro;
  /** The date of the competition: the schedule shares it. */
  fechaCompetencia: string;
}

/**
 * CompetenciaProgramacionEditor — schedule an encounter.
 *
 * The day and the two times are collected apart and the payload composes the
 * two instants: the mutation hook owns that composition
 * (`contract/next-app-architecture-contract.md` §5).
 */
export function CompetenciaProgramacionEditor({
  competenciaId,
  encuentro,
  fechaCompetencia,
}: CompetenciaProgramacionEditorProps) {
  const mutacion = useProgramarEncuentro();
  const envio = useEnvioEditor<VariablesProgramacion["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Programar encuentro"
      descripcion="El intervalo es positivo y el mismo equipo nunca juega dos encuentros a la vez."
      esquema={EncuentroProgramacionFormSchema}
      campos={CAMPOS_PROGRAMACION}
      initialData={{
        fecha: fechaCompetencia,
        hora_inicio: horaDe(encuentro.inicio_programado),
        hora_fin: horaDe(encuentro.fin_programado),
        motivo: "",
      }}
      onSubmit={(datos) => {
        mutacion.reset();
        return envio.enviar(datos);
      }}
      error={mutacion.error}
      onReintentar={() => {
        mutacion.reset();
        void envio.reintentar();
      }}
      isPending={mutacion.isPending}
      submitLabel="Programar encuentro"
    />
  );
}
