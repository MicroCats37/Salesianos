"use client";

import { Loader2 } from "lucide-react";
import { useId } from "react";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type { FormField } from "@/components/genericForm/GenericInput";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import {
  useConfirmarAvance,
  usePrevisualizarAvance,
  type VariablesAvance,
} from "../../hooks";
import { AvanceConfirmarFormSchema, type Encuentro } from "../../schemas";
import { CompetenciaErrorAlert } from "../CompetenciaErrorAlert";
import { CompetenciaCampo } from "../editors/CompetenciaCampo";
import { useEnvioEditor } from "../editors/useEnvioEditor";

/**
 * CompetenciaAvanceDialog — the propagation of the winner to the next
 * encounter.
 *
 * The flow is ALWAYS a proposal and a confirmation:
 *
 * 1. the PREVIEW proposes the placement and it NEVER writes,
 * 2. the administrator confirms it with an audited motive.
 *
 * A blocked destination is not an error of the request: it is reported in the
 * proposal and the confirmation stays disabled
 * (`sdd/enfrentamientos-competencias/spec`, requirement "Ganador, marcador y
 * propagación").
 */

/** Fields of the confirmation of the advance. */
const CAMPOS_AVANCE: FormField[] = [
  {
    name: "motivo",
    label: "Motivo de la propagación",
    type: "textarea",
    required: true,
    maxLength: 500,
    helperText: "La propagación se coloca una sola vez y queda auditada.",
    containerClassName: "col-span-12",
  },
];

export interface CompetenciaAvanceDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter whose winner is being propagated. */
  encuentro: Encuentro;
}

/**
 * CompetenciaAvanceDialog — propose and confirm the propagation.
 */
export function CompetenciaAvanceDialog({
  open,
  onOpenChange,
  competenciaId,
  encuentro,
}: CompetenciaAvanceDialogProps) {
  const formId = useId();
  const mutacion = useConfirmarAvance();
  const previa = usePrevisualizarAvance(encuentro.id, open);
  const envio = useEnvioEditor<VariablesAvance["datos"]>((datos) =>
    mutacion.mutateAsync({
      competenciaId,
      encuentroId: encuentro.id,
      expectedVersion: encuentro.version,
      datos,
    }),
  );

  const propuesta = previa.data?.success ? previa.data.data : null;
  const bloqueado = propuesta?.bloqueado === true;
  const yaPropagado = propuesta?.ya_propagado === true;
  const confirmable =
    Boolean(propuesta) && !bloqueado && !yaPropagado && !previa.isPending;

  return (
    <GenericModal
      open={open}
      onOpenChange={onOpenChange}
      preventClose={mutacion.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title="Propagar el ganador"
          description="La propuesta se confirma con un motivo: el ganador se coloca una sola vez."
        />

        <GenericModal.Body className="space-y-4">
          {previa.isPending ? (
            <p className="text-xs text-slate-500">Calculando la propuesta…</p>
          ) : null}

          {previa.error ? (
            <CompetenciaErrorAlert
              error={previa.error}
              reintentarLabel="Recalcular la propuesta"
              onReintentar={() => {
                void previa.refetch();
              }}
            />
          ) : null}

          {propuesta ? (
            <dl
              aria-label="Propuesta del avance"
              className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="font-black uppercase tracking-wider text-slate-500">
                  Destino
                </dt>
                <dd className="font-bold text-slate-800">
                  {propuesta.siguiente_encuentro_id}
                </dd>
              </div>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="font-black uppercase tracking-wider text-slate-500">
                  Slot
                </dt>
                <dd className="font-bold text-slate-800">
                  {propuesta.slot_destino}
                </dd>
              </div>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="font-black uppercase tracking-wider text-slate-500">
                  Ganador
                </dt>
                <dd className="font-bold text-slate-800">
                  {propuesta.ganador_id}
                </dd>
              </div>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="font-black uppercase tracking-wider text-slate-500">
                  Ocupante actual
                </dt>
                <dd className="font-bold text-slate-800">
                  {propuesta.ocupante_actual_id ?? "—"}
                </dd>
              </div>
            </dl>
          ) : null}

          {bloqueado ? (
            <p
              aria-live="polite"
              className="text-xs font-medium text-destructive"
            >
              El destino está bloqueado:{" "}
              {propuesta?.motivo_bloqueo ?? "sin detalle"}
            </p>
          ) : null}

          {yaPropagado ? (
            <p
              aria-live="polite"
              className="text-xs font-medium text-slate-600"
            >
              El ganador ya se propagó a este destino: no hay nada que
              confirmar.
            </p>
          ) : null}

          <GenericForm
            formId={formId}
            schema={AvanceConfirmarFormSchema}
            fields={CAMPOS_AVANCE}
            initialData={{ motivo: "" }}
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
                {CAMPOS_AVANCE.map((campo) => (
                  <CompetenciaCampo key={campo.name} campo={campo} />
                ))}
              </div>
            )}
          </GenericForm>

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
            disabled={mutacion.isPending || !confirmable}
          >
            {mutacion.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            Confirmar avance
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}
