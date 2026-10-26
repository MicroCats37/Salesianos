"use client";

import { Loader2, ShieldAlert } from "lucide-react";
import { useEffect, useId, useState } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type { FormField } from "@/components/genericForm/GenericInput";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import {
  useConfirmarCorreccion,
  usePrevisualizarCorreccion,
  type VariablesCorreccion,
} from "../../hooks";
import { CorreccionFormSchema, type Encuentro } from "../../schemas";
import { CompetenciaErrorAlert } from "../CompetenciaErrorAlert";
import { CompetenciaCampo } from "../editors/CompetenciaCampo";
import { useEnvioEditor } from "../editors/useEnvioEditor";

/**
 * CompetenciaCorreccionDialog — the correction of the AUTHORITATIVE winner
 * of an encounter.
 *
 * The correction is ALWAYS a preview and a confirmation:
 *
 * 1. the PREVIEW exposes the impact over EVERY descendant of the link and it
 *    NEVER writes,
 * 2. the administrator confirms it with an audited motive,
 * 3. when a descendant already started, finished or was cancelled, the
 *    correction changes NOTHING unless the administrator ACCEPTS the exposed
 *    impact: there is never a silent cascade
 *    (`sdd/enfrentamientos-competencias/spec`, requirement "Overrides y
 *    correcciones auditables").
 */

/** Fields of the correction. */
const CAMPOS_CORRECCION: FormField[] = [
  {
    name: "ganador_id",
    label: "Nuevo ganador",
    type: "select",
    required: true,
    helperText: "Solo los equipos que ocupan un slot pueden ganar.",
    containerClassName: "col-span-12",
  },
  {
    name: "motivo",
    label: "Motivo de la corrección",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText: "La corrección es siempre auditada: el motivo es obligatorio.",
    containerClassName: "col-span-12",
  },
  {
    name: "acepta_impacto",
    label: "Acepto el impacto de la corrección",
    type: "checkbox",
    description:
      "Obligatorio cuando un dependiente ya empezó, terminó o fue cancelado.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaCorreccionDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter whose winner is being corrected. */
  encuentro: Encuentro;
}

/**
 * CompetenciaCorreccionDialog — correct the winner of an encounter.
 *
 * The impact of the correction is EXPOSED before the confirmation and the
 * acceptance of the impact is EXPLICIT: the confirm button stays disabled
 * until the administrator accepts it.
 */
export function CompetenciaCorreccionDialog({
  open,
  onOpenChange,
  competenciaId,
  encuentro,
}: CompetenciaCorreccionDialogProps) {
  const formId = useId();
  const mutacion = useConfirmarCorreccion();

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

  const [ganadorId, setGanadorId] = useState(() =>
    ganadorPropuesto(encuentro, opciones),
  );
  const [aceptaImpacto, setAceptaImpacto] = useState(false);

  const previa = usePrevisualizarCorreccion(encuentro.id, ganadorId, open);
  const envio = useEnvioEditor<VariablesCorreccion["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  const impacto = previa.data?.success ? previa.data.data : null;
  const requiereOverride = impacto?.requiere_override === true;

  const campos = CAMPOS_CORRECCION.map((campo) =>
    campo.name === "ganador_id" ? { ...campo, options: opciones } : campo,
  );

  const faltaAceptacion = requiereOverride && !aceptaImpacto;

  return (
    <GenericModal
      open={open}
      onOpenChange={onOpenChange}
      preventClose={mutacion.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title="Corregir el ganador"
          description="La corrección expone su impacto: nada se reescribe en silencio."
        />

        <GenericModal.Body className="space-y-4">
          <GenericForm
            formId={formId}
            schema={CorreccionFormSchema}
            fields={campos}
            initialData={{
              ganador_id: ganadorId,
              motivo: "",
              acepta_impacto: false,
            }}
            onSubmit={async (datos) => {
              mutacion.reset();
              setGanadorId(datos.ganador_id);
              await envio.enviar(datos);
              onOpenChange(false);
            }}
            isLoading={mutacion.isPending}
            skipFooter
          >
            {() => (
              <>
                <div className="grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-12">
                  {campos.map((campo) => (
                    <CompetenciaCampo key={campo.name} campo={campo} />
                  ))}
                </div>

                <ObservadorCorreccion
                  onGanador={setGanadorId}
                  onAcepta={setAceptaImpacto}
                />
              </>
            )}
          </GenericForm>

          {impacto ? (
            <section
              aria-label="Impacto de la corrección"
              className="space-y-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs"
            >
              <p className="flex items-center gap-2 font-black uppercase tracking-wider text-amber-800">
                <ShieldAlert className="h-4 w-4" aria-hidden="true" />
                Impacto de la corrección
              </p>

              <p className="font-medium text-amber-900">
                {requiereOverride
                  ? "Un dependiente ya empezó, terminó o fue cancelado: la corrección necesita tu aceptación explícita y un motivo."
                  : "Los dependientes que todavía no empezaron se ajustan de forma asistida y su resultado se limpia."}
              </p>

              {impacto.descendientes.length === 0 ? (
                <p className="text-slate-600">
                  Este encuentro no tiene dependientes: la corrección no alcanza
                  ningún otro cuadro.
                </p>
              ) : (
                <ul className="space-y-2">
                  {impacto.descendientes.map((descendiente) => (
                    <li
                      key={`${descendiente.encuentro_id}-${descendiente.slot}`}
                      className="rounded-lg border border-amber-200 bg-white p-2"
                    >
                      <p className="font-bold text-slate-800">
                        {descendiente.encuentro_id} · {descendiente.slot}
                      </p>
                      <p className="text-slate-600">
                        Estado: {descendiente.estado} · Ocupante:{" "}
                        {descendiente.ocupante_actual_id ?? "—"}
                      </p>
                      <p className="text-slate-600">
                        {descendiente.se_reemplaza
                          ? "El ocupante se reemplaza por el ganador corregido."
                          : "El ocupante no se reemplaza."}
                        {descendiente.se_limpia_resultado
                          ? " Su resultado se limpia."
                          : " Su resultado se conserva."}
                      </p>
                      {descendiente.bloqueado ? (
                        <p className="font-medium text-destructive">
                          Bloqueado:{" "}
                          {descendiente.motivo_bloqueo ?? "sin detalle"}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}

          {previa.error ? (
            <CompetenciaErrorAlert
              error={previa.error}
              reintentarLabel="Recalcular el impacto"
              onReintentar={() => {
                void previa.refetch();
              }}
            />
          ) : null}

          {mutacion.error ? (
            <CompetenciaErrorAlert
              error={mutacion.error}
              onReintentar={() => {
                mutacion.reset();
                void envio.reintentar();
              }}
            />
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
            disabled={
              mutacion.isPending || !impacto || faltaAceptacion || !ganadorId
            }
          >
            {mutacion.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            Confirmar corrección
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}

/**
 * ObservadorCorreccion — the SMART FIELD that lifts the decisions of the
 * form to the dialog.
 *
 * The preview of the impact depends on the winner that the administrator
 * chose and the confirmation depends on the acceptance of the impact: both
 * live in the form, and the dialog needs to know about them
 * (`contract/smart.md` §2).
 */
function ObservadorCorreccion({
  onGanador,
  onAcepta,
}: {
  onGanador: (ganadorId: string) => void;
  onAcepta: (acepta: boolean) => void;
}) {
  const { control } = useFormContext();
  const ganadorId = useWatch({ control, name: "ganador_id" }) as string;
  const acepta = useWatch({ control, name: "acepta_impacto" }) as boolean;

  useEffect(() => {
    onGanador(ganadorId);
  }, [ganadorId, onGanador]);

  useEffect(() => {
    onAcepta(acepta);
  }, [acepta, onAcepta]);

  return null;
}

/**
 * The winner that the correction proposes: the participant that is NOT the
 * current winner of the encounter.
 */
function ganadorPropuesto(
  encuentro: Encuentro,
  opciones: { label: string; value: string }[],
): string {
  if (opciones.length === 0) return "";
  const otro = opciones.find((opcion) => opcion.value !== encuentro.ganador_id);
  return (otro ?? opciones[0]).value;
}
