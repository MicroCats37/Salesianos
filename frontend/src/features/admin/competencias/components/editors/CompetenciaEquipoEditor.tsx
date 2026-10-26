"use client";

import type { FormField } from "@/components/genericForm/GenericInput";
import {
  useActualizarEquipoCompetencia,
  useCrearEquipoCompetencia,
  type VariablesEquipoAlta,
  type VariablesEquipoEdicion,
} from "../../hooks";
import type { CompetenciaEquipo } from "../../schemas";
import {
  CompetenciaEquipoCreateFormSchema,
  CompetenciaEquipoUpdateFormSchema,
} from "../../schemas";
import { CompetenciaEditorShell } from "./CompetenciaEditorShell";
import { useEnvioEditor } from "./useEnvioEditor";

/**
 * The editors of the TEAMS of a competition — the MANUAL seed of the bracket.
 *
 * The order is NEVER chosen by the system: the administrator types it and
 * the change is audited with its motive
 * (`sdd/enfrentamientos-competencias/spec`, requirement "Equipos, pertenencia
 * y orden").
 */

/** Fields of the registration of a team. */
const CAMPOS_EQUIPO_ALTA: FormField[] = [
  {
    name: "equipo_id",
    label: "Identificador del equipo",
    type: "text",
    required: true,
    placeholder: "00000000-0000-0000-0000-000000000000",
    helperText:
      "El equipo debe estar activo y pertenecer al evento, la disciplina y la categoría de la competencia.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "orden",
    label: "Orden en el cuadro",
    type: "number",
    required: true,
    min: 1,
    helperText: "La semilla es manual: el sistema nunca la elige.",
    containerClassName: "col-span-12 md:col-span-6",
  },
];

/** Fields of the edition of a participation. */
const CAMPOS_EQUIPO_EDICION: FormField[] = [
  {
    name: "orden",
    label: "Orden en el cuadro",
    type: "number",
    required: true,
    min: 1,
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "estado",
    label: "Estado de la participación",
    type: "select",
    required: true,
    options: [
      { label: "Activo", value: "ACTIVO" },
      { label: "Retirado", value: "RETIRADO" },
    ],
    helperText: "Un equipo retirado conserva su historia: nunca se borra.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "motivo",
    label: "Motivo del cambio",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText: "Entre 5 y 500 caracteres: el cambio queda auditado.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaEquipoAltaEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
}

/**
 * CompetenciaEquipoAltaEditor — register a team in the bracket with its
 * MANUAL order.
 */
export function CompetenciaEquipoAltaEditor({
  competenciaId,
}: CompetenciaEquipoAltaEditorProps) {
  const mutacion = useCrearEquipoCompetencia();
  const envio = useEnvioEditor<VariablesEquipoAlta["datos"]>((datos) =>
    mutacion.mutateAsync({ competenciaId, datos }),
  );

  return (
    <CompetenciaEditorShell
      titulo="Incorporar equipo"
      descripcion="El equipo entra con el orden que indiques: la semilla es siempre manual."
      esquema={CompetenciaEquipoCreateFormSchema}
      campos={CAMPOS_EQUIPO_ALTA}
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
      submitLabel="Incorporar equipo"
    />
  );
}

export interface CompetenciaEquipoEdicionEditorProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The participation that is being edited. */
  equipo: CompetenciaEquipo;
  /** The action that closes the editor. */
  onCancel?: () => void;
}

/**
 * CompetenciaEquipoEdicionEditor — change the manual order or the state of
 * a participation.
 *
 * The optimistic lock travels with the version that the server returned: a
 * stale version fails with 409 `RESOURCE_CHANGED` and NOTHING is written.
 */
export function CompetenciaEquipoEdicionEditor({
  competenciaId,
  equipo,
  onCancel,
}: CompetenciaEquipoEdicionEditorProps) {
  const mutacion = useActualizarEquipoCompetencia();
  const envio = useEnvioEditor<VariablesEquipoEdicion["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      equipoId: equipo.id,
      expectedVersion: equipo.version,
      datos,
    }),
  );

  return (
    <CompetenciaEditorShell
      titulo={`Editar ${equipo.equipo_nombre}`}
      descripcion="El orden es una decisión manual y auditada del administrador."
      esquema={CompetenciaEquipoUpdateFormSchema}
      campos={CAMPOS_EQUIPO_EDICION}
      initialData={{
        orden: equipo.orden,
        estado: equipo.estado === "RETIRADO" ? "RETIRADO" : "ACTIVO",
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
      submitLabel="Guardar cambios"
      onCancel={onCancel}
    />
  );
}
