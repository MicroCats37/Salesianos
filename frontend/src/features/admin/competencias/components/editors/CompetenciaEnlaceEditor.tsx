"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import {
  useDesenlazarEncuentro,
  useEnlazarEncuentro,
  type VariablesDesenlace,
  type VariablesEnlace,
} from "../../hooks";
import {
  type Encuentro,
  EncuentroDesenlaceFormSchema,
  EncuentroEnlaceFormSchema,
} from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editors of the LINKS of the bracket.
 *
 * The link and its destination slot are written TOGETHER and the link always
 * points forward (to a later round of the same competition), so a cycle can
 * never be built. An invalid link fails with 422 `INVALID_LINK`.
 */

/** Fields of the link of an encounter with the next one. */
const CAMPOS_ENLACE: FormField[] = [
  {
    name: "siguiente_encuentro_id",
    label: "Encuentro destino (UUID)",
    type: "text",
    required: true,
    placeholder: "00000000-0000-0000-0000-000000000000",
    helperText: "El destino es un encuentro de una ronda posterior.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "slot_destino",
    label: "Slot del destino",
    type: "select",
    required: true,
    options: [
      { label: "Participante 1", value: "PARTICIPANTE_1" },
      { label: "Participante 2", value: "PARTICIPANTE_2" },
    ],
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "motivo",
    label: "Motivo del enlace",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText: "El enlace queda auditado: el motivo es obligatorio.",
    containerClassName: "col-span-12",
  },
];

/** Fields of the removal of the link of an encounter. */
const CAMPOS_DESENLACE: FormField[] = [
  {
    name: "motivo",
    label: "Motivo de la eliminación",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText:
      "Una propagación ya aplicada no se puede dejar huérfana: esa reescritura la posee la corrección.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaEnlaceEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter that is being linked. */
  encuentro: Encuentro;
}

/**
 * CompetenciaEnlaceEditor — link an encounter to the next one.
 *
 * The link and the slot travel together: they are the same audited decision.
 */
export function CompetenciaEnlaceEditor({
  competenciaId,
  encuentro,
}: CompetenciaEnlaceEditorProps) {
  const mutacion = useEnlazarEncuentro();
  const envio = useEnvioEditor<VariablesEnlace["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Enlazar con el siguiente encuentro"
      descripcion="El enlace y su slot se escriben juntos y siempre apuntan a una ronda posterior."
      esquema={EncuentroEnlaceFormSchema}
      campos={CAMPOS_ENLACE}
      initialData={{
        siguiente_encuentro_id: "",
        slot_destino: "PARTICIPANTE_1" as const,
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
      submitLabel="Enlazar encuentro"
    />
  );
}

export interface CompetenciaDesenlaceEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter whose link is being removed. */
  encuentro: Encuentro;
}

/**
 * CompetenciaDesenlaceEditor — remove the link of an encounter.
 *
 * Both fields travel together and the motive is audited: the link is never
 * removed in silence.
 */
export function CompetenciaDesenlaceEditor({
  competenciaId,
  encuentro,
}: CompetenciaDesenlaceEditorProps) {
  const mutacion = useDesenlazarEncuentro();
  const envio = useEnvioEditor<VariablesDesenlace["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Eliminar el enlace"
      descripcion="El enlace se elimina con su motivo: nada se borra en silencio."
      esquema={EncuentroDesenlaceFormSchema}
      campos={CAMPOS_DESENLACE}
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
      submitLabel="Eliminar enlace"
    />
  );
}
