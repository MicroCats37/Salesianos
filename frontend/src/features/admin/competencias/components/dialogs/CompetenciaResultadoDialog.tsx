"use client";

import { Loader2 } from "lucide-react";
import { useId } from "react";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type { FormField } from "@/components/genericForm/GenericInput";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import {
  useRegistrarResultadoEncuentro,
  type VariablesResultado,
} from "../../hooks";
import { type Encuentro, ResultadoEncuentroFormSchema } from "../../schemas";
import { CompetenciaErrorAlert } from "../CompetenciaErrorAlert";
import { CompetenciaCampo } from "../editors/CompetenciaCampo";
import { useEnvioEditor } from "../editors/useEnvioEditor";

/**
 * CompetenciaResultadoDialog — the registration of the AUTHORITATIVE result
 * of an encounter.
 *
 * The winner is authoritative and it MUST occupy one of the two slots. The
 * scores are optional and purely informative: they never determine nor
 * contradict the winner
 * (`sdd/enfrentamientos-competencias/spec`, requirement "Ganador, marcador y
 * propagación").
 */

/** Fields of the result. */
const CAMPOS_RESULTADO: FormField[] = [
  {
    name: "ganador_id",
    label: "Ganador",
    type: "select",
    required: true,
    helperText: "El ganador es el único que decide el resultado.",
    containerClassName: "col-span-12",
  },
  {
    name: "puntaje_1",
    label: "Puntaje del participante 1",
    type: "number",
    min: 0,
    helperText: "Opcional e informativo: no determina al ganador.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "puntaje_2",
    label: "Puntaje del participante 2",
    type: "number",
    min: 0,
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "marcador_detalle",
    label: "Detalle del marcador",
    type: "text",
    maxLength: 500,
    placeholder: "3 sets a 2",
    containerClassName: "col-span-12",
  },
  {
    name: "motivo",
    label: "Motivo del registro",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText: "Registrar un resultado es una decisión auditada.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaResultadoDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter whose result is being registered. */
  encuentro: Encuentro;
}

/**
 * CompetenciaResultadoDialog — register the result of an encounter.
 *
 * The dialog owns NOTHING but the presentation: the payload travels from the
 * mutation hook with the version that the server returned.
 */
export function CompetenciaResultadoDialog({
  open,
  onOpenChange,
  competenciaId,
  encuentro,
}: CompetenciaResultadoDialogProps) {
  const formId = useId();
  const mutacion = useRegistrarResultadoEncuentro();
  const envio = useEnvioEditor<VariablesResultado["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  const opciones = [
    ...(encuentro.participante_1_id
      ? [
          {
            label: encuentro.participante_1_nombre ?? "Participante 1",
            value: encuentro.participante_1_id,
          },
        ]
      : []),
    ...(encuentro.participante_2_id
      ? [
          {
            label: encuentro.participante_2_nombre ?? "Participante 2",
            value: encuentro.participante_2_id,
          },
        ]
      : []),
  ];

  const campos = CAMPOS_RESULTADO.map((campo) =>
    campo.name === "ganador_id" ? { ...campo, options: opciones } : campo,
  );

  const sinParticipantes = opciones.length === 0;

  return (
    <GenericModal
      open={open}
      onOpenChange={onOpenChange}
      preventClose={mutacion.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title="Registrar resultado"
          description="El ganador es el único autoritativo: los puntajes solo informan."
        />

        <GenericModal.Body>
          {sinParticipantes ? (
            <p className="text-sm font-medium text-destructive">
              El encuentro no tiene participantes: el resultado se registra
              cuando los equipos están en sus slots.
            </p>
          ) : null}

          <GenericForm
            formId={formId}
            schema={ResultadoEncuentroFormSchema}
            fields={campos}
            initialData={{
              ganador_id: encuentro.participante_1_id ?? "",
              puntaje_1: null,
              puntaje_2: null,
              marcador_detalle: "",
              motivo: "",
            }}
            onSubmit={async (datos) => {
              mutacion.reset();
              await envio.enviar(datos);
              onOpenChange(false);
            }}
            isLoading={mutacion.isPending}
            skipFooter
          >
            {() => (
              <div className="grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-12">
                {campos.map((campo) => (
                  <CompetenciaCampo key={campo.name} campo={campo} />
                ))}
              </div>
            )}
          </GenericForm>

          {mutacion.error ? (
            <div className="mt-3">
              <CompetenciaErrorAlert
                error={mutacion.error}
                onReintentar={() => {
                  mutacion.reset();
                  void envio.reintentar();
                }}
              />
            </div>
          ) : null}
        </GenericModal.Body>

        <GenericModal.Footer>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={mutacion.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form={formId}
            disabled={mutacion.isPending || sinParticipantes}
          >
            {mutacion.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            Registrar resultado
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}
