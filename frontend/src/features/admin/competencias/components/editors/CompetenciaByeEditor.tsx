"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import { useConfigurarByeEncuentro, type VariablesBye } from "../../hooks";
import { type Encuentro, EncuentroByeFormSchema } from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editor of the MANUAL bye.
 *
 * The system NEVER chooses a bye by itself: the administrator configures it
 * and the change is audited with its motive
 * (`sdd/enfrentamientos-competencias/spec`, requirement "Rondas, byes y
 * cuadros incompletos").
 */

/** Fields of the manual bye. */
const CAMPOS_BYE: FormField[] = [
  {
    name: "motivo",
    label: "Motivo del bye",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText:
      "El bye es una decisión manual y auditada: el motivo es obligatorio.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaByeEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter that receives the bye. */
  encuentro: Encuentro;
}

/**
 * CompetenciaByeEditor — configure the MANUAL bye of an encounter.
 *
 * A bye has exactly one participant, no schedule and no score, and it is
 * final: it is never deleted, only audited.
 */
export function CompetenciaByeEditor({
  competenciaId,
  encuentro,
}: CompetenciaByeEditorProps) {
  const mutacion = useConfigurarByeEncuentro();
  const envio = useEnvioEditor<VariablesBye["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Configurar bye manual"
      descripcion="El bye lo asigna el administrador: el sistema nunca lo elige por sí solo."
      esquema={EncuentroByeFormSchema}
      campos={CAMPOS_BYE}
      initialData={{ motivo: "" }}
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
      submitLabel="Configurar bye"
    />
  );
}
