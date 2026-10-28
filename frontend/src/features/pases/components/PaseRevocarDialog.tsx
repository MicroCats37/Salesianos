"use client";

import { Loader2, TriangleAlert } from "lucide-react";
import { useId } from "react";
import { useFormContext } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import {
  type FormField,
  GenericInput,
} from "@/components/genericForm/GenericInput";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import { useRevocarBeneficiario } from "../hooks/useRevocarBeneficiario";
import type { PaseBeneficiarioAuditado } from "../schemas";
import { paseRevocarBeneficiarioFormSchema } from "../schemas";
import { pasePersonaNombre } from "../utils/pase.beneficiario";

/**
 * PaseRevocarDialog — the PERMANENT revocation of a nominative right.
 *
 * Two decisions of this dialog:
 *
 * 1. The revocation asks for the AUDITED motive: it is mandatory and it
 *    travels to the backend, which keeps it with the right.
 * 2. The dialog warns that the revocation is NOT a transfer: the slot is
 *    consumed forever and the pass never reaches somebody else.
 *
 * The component handles ZERO raw error logic: the failures travel through
 * `handleApiError` inside the service and reach the buyer through the alert
 * of the dialog and the toast adapter.
 */

/** Fields of the revocation. */
const CAMPOS_MOTIVO: FormField[] = [
  {
    name: "motivo",
    label: "Motivo de la revocación",
    type: "textarea",
    required: true,
    maxLength: 1000,
    helperText: "Queda registrado como parte de la auditoría.",
    containerClassName: "col-span-12",
  },
];

/**
 * PaseRevocarCampo — ONE field of the dialog.
 *
 * The field is rendered with the shared `GenericInput`, so the label, the
 * helper text and the error message are the shared ones of the application.
 * The state comes from the context of `GenericForm`: the component NEVER
 * owns a value and NEVER validates by itself (`contract/smart.md` §2).
 */
function PaseRevocarCampo({ campo }: { campo: FormField }) {
  const { register, control, formState } = useFormContext();

  return (
    <GenericInput
      field={campo}
      register={register}
      control={control}
      errors={formState.errors}
    />
  );
}

/** The grid of the fields of the dialog. */
function Campos({ campos }: { campos: FormField[] }) {
  return (
    <div className="grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-12">
      {campos.map((campo) => (
        <PaseRevocarCampo key={campo.name} campo={campo} />
      ))}
    </div>
  );
}

export interface PaseRevocarDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The batch that owns the right. */
  compraId: string;
  /** The person whose right is revoked — `null` closes the dialog. */
  beneficiario: PaseBeneficiarioAuditado | null;
}

export function PaseRevocarDialog({
  open,
  onOpenChange,
  compraId,
  beneficiario,
}: PaseRevocarDialogProps) {
  const formId = useId();
  const revocar = useRevocarBeneficiario();

  return (
    <GenericModal
      open={open && beneficiario !== null}
      onOpenChange={onOpenChange}
      preventClose={revocar.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title="Revocar el pase de esta persona"
          description="La revocación es permanente y queda auditada."
        />

        <GenericModal.Body className="space-y-4">
          <div
            role="alert"
            className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900"
          >
            <TriangleAlert
              className="mt-0.5 size-5 shrink-0"
              aria-hidden="true"
            />
            <div className="space-y-1">
              <p className="font-black">
                {beneficiario
                  ? `El pase del slot ${beneficiario.slot} de ${pasePersonaNombre(beneficiario)} se revoca ahora.`
                  : "El pase se revoca ahora."}
              </p>
              <p>
                El slot queda consumido para siempre y el pase NO se puede
                transferir a otra persona. La organización puede cancelar la
                compra completa si corresponde.
              </p>
            </div>
          </div>

          <GenericForm
            formId={formId}
            schema={paseRevocarBeneficiarioFormSchema}
            fields={CAMPOS_MOTIVO}
            initialData={{ motivo: "" }}
            onSubmit={async (datos) => {
              if (!beneficiario) return;
              await revocar.mutateAsync({
                compraId,
                personaId: beneficiario.persona_id,
                motivo: datos.motivo,
              });
              onOpenChange(false);
            }}
            isLoading={revocar.isPending}
            skipFooter
          >
            {() => <Campos campos={CAMPOS_MOTIVO} />}
          </GenericForm>

          {revocar.error ? (
            <p role="alert" className="text-xs font-medium text-destructive">
              {revocar.error.message}
            </p>
          ) : null}
        </GenericModal.Body>

        <GenericModal.Footer>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={revocar.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form={formId}
            variant="destructive"
            disabled={revocar.isPending}
          >
            {revocar.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            Revocar el pase
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}
