"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import {
  useActualizarRondaCompetencia,
  useCrearRondaCompetencia,
  type VariablesRondaAlta,
  type VariablesRondaEdicion,
} from "../../hooks";
import {
  type Ronda,
  RondaCreateFormSchema,
  RondaUpdateFormSchema,
} from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editors of the ROUNDS of a competition — the columns of the bracket.
 *
 * The label and the order are unique inside the bracket and they are MANUAL:
 * a round without encounters stays visible and editable.
 */

/** Fields of the creation of a round. */
const CAMPOS_RONDA_ALTA: FormField[] = [
  {
    name: "etiqueta",
    label: "Etiqueta de la ronda",
    type: "text",
    required: true,
    maxLength: 100,
    placeholder: "Octavos de final",
    helperText: "La etiqueta y el orden son únicos dentro del cuadro.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "orden",
    label: "Orden de la ronda",
    type: "number",
    required: true,
    min: 1,
    containerClassName: "col-span-12 md:col-span-6",
  },
];

/** Fields of the edition of a round. */
const CAMPOS_RONDA_EDICION: FormField[] = [
  {
    name: "etiqueta",
    label: "Etiqueta de la ronda",
    type: "text",
    required: true,
    maxLength: 100,
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "orden",
    label: "Orden de la ronda",
    type: "number",
    required: true,
    min: 1,
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "motivo",
    label: "Motivo del cambio",
    type: "textarea",
    maxLength: 500,
    helperText:
      "Opcional en una ronda. Cuando mueve la ronda, el motivo queda auditado.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaRondaAltaEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
}

/** CompetenciaRondaAltaEditor — create a round of the bracket. */
export function CompetenciaRondaAltaEditor({
  competenciaId,
}: CompetenciaRondaAltaEditorProps) {
  const mutacion = useCrearRondaCompetencia();
  const envio = useEnvioEditor<VariablesRondaAlta["datos"]>((datos) =>
    mutacion.mutateAsync({ competenciaId, datos }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Nueva ronda"
      descripcion="Las rondas son las columnas del cuadro: una ronda vacía sigue siendo legible."
      esquema={RondaCreateFormSchema}
      campos={CAMPOS_RONDA_ALTA}
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
      submitLabel="Registrar ronda"
    />
  );
}

export interface CompetenciaRondaEdicionEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The round that is being edited. */
  ronda: Ronda;
  /** The action that closes the editor. */
  onCancel?: () => void;
}

/**
 * CompetenciaRondaEdicionEditor — change the label or the order of a round.
 *
 * A round is never deleted: it is invalidated and it keeps its history.
 */
export function CompetenciaRondaEdicionEditor({
  competenciaId,
  ronda,
  onCancel,
}: CompetenciaRondaEdicionEditorProps) {
  const mutacion = useActualizarRondaCompetencia();
  const envio = useEnvioEditor<VariablesRondaEdicion["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      rondaId: ronda.id,
      expectedVersion: ronda.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo={`Editar ${ronda.etiqueta}`}
      descripcion="La ronda conserva su historia: solo puede invalidarse."
      esquema={RondaUpdateFormSchema}
      campos={CAMPOS_RONDA_EDICION}
      initialData={{ etiqueta: ronda.etiqueta, orden: ronda.orden, motivo: "" }}
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
      submitLabel="Guardar cambios"
      onCancel={onCancel}
    />
  );
}
