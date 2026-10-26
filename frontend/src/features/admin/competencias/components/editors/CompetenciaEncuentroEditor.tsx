"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import {
  useActualizarParticipantesEncuentro,
  useCrearEncuentroCompetencia,
  type VariablesEncuentroAlta,
  type VariablesParticipantes,
} from "../../hooks";
import {
  type Encuentro,
  EncuentroCreateFormSchema,
  EncuentroParticipantesFormSchema,
} from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editors of the ENCOUNTERS of a competition.
 *
 * Both participants are OPTIONAL on purpose: an empty or partial bracket
 * must stay readable and editable without inventing a participant
 * (`sdd/enfrentamientos-competencias/spec`, requirement "Rondas, byes y
 * cuadros incompletos").
 */

/** Fields of the creation of an encounter. */
const CAMPOS_ENCUENTRO_ALTA: FormField[] = [
  {
    name: "ronda_id",
    label: "Ronda (UUID)",
    type: "text",
    required: true,
    placeholder: "00000000-0000-0000-0000-000000000000",
    helperText: "La ronda a la que pertenece el encuentro.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "orden",
    label: "Orden en la ronda",
    type: "number",
    required: true,
    min: 1,
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "participante_1_id",
    label: "Participante 1 (UUID, opcional)",
    type: "text",
    placeholder: "00000000-0000-0000-0000-000000000000",
    helperText: "Puede quedar vacío: el cuadro parcial es válido.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "participante_2_id",
    label: "Participante 2 (UUID, opcional)",
    type: "text",
    placeholder: "00000000-0000-0000-0000-000000000000",
    containerClassName: "col-span-12 md:col-span-6",
  },
];

/** Fields of the edition of the participants of an encounter. */
const CAMPOS_PARTICIPANTES: FormField[] = [
  {
    name: "participante_1_id",
    label: "Participante 1 (UUID, opcional)",
    type: "text",
    placeholder: "00000000-0000-0000-0000-000000000000",
    helperText: "Un espacio vacío deja el slot sin equipo.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "participante_2_id",
    label: "Participante 2 (UUID, opcional)",
    type: "text",
    placeholder: "00000000-0000-0000-0000-000000000000",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "motivo",
    label: "Motivo del cambio",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText:
      "Mover un equipo es una decisión auditada: el motivo es obligatorio.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaEncuentroAltaEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
}

/** CompetenciaEncuentroAltaEditor — create an encounter in a round. */
export function CompetenciaEncuentroAltaEditor({
  competenciaId,
}: CompetenciaEncuentroAltaEditorProps) {
  const mutacion = useCrearEncuentroCompetencia();
  const envio = useEnvioEditor<VariablesEncuentroAlta["datos"]>((datos) =>
    mutacion.mutateAsync({ competenciaId, datos }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Nuevo encuentro"
      descripcion="Los dos participantes son opcionales: un cuadro parcial se edita sin inventar equipos."
      esquema={EncuentroCreateFormSchema}
      campos={CAMPOS_ENCUENTRO_ALTA}
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
      submitLabel="Registrar encuentro"
    />
  );
}

export interface CompetenciaEncuentroParticipantesEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter whose slots are being edited. */
  encuentro: Encuentro;
}

/**
 * CompetenciaEncuentroParticipantesEditor — move the teams of the two slots.
 *
 * Moving a slot ALWAYS demands an audited motive: the domain rejects the
 * command without it (422 `REASON_REQUIRED`).
 */
export function CompetenciaEncuentroParticipantesEditor({
  competenciaId,
  encuentro,
}: CompetenciaEncuentroParticipantesEditorProps) {
  const mutacion = useActualizarParticipantesEncuentro();
  const envio = useEnvioEditor<VariablesParticipantes["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Participantes del encuentro"
      descripcion="Los dos slots admiten un equipo o ninguno mientras el encuentro esté incompleto."
      esquema={EncuentroParticipantesFormSchema}
      campos={CAMPOS_PARTICIPANTES}
      initialData={{
        participante_1_id: encuentro.participante_1_id ?? "",
        participante_2_id: encuentro.participante_2_id ?? "",
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
      submitLabel="Guardar participantes"
    />
  );
}
