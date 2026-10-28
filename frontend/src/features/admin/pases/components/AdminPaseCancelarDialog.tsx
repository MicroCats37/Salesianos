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
import { useCancelarCompraPase } from "../hooks/useAdminPaseComandos";
import { AdminPaseCancelarFormSchema } from "../schemas";
import { adminPaseCancelacionAviso } from "../utils/admin.pase.utils";

/**
 * AdminPaseCancelarDialog — the administrative cancellation of a pass
 * purchase.
 *
 * Two decisions of this dialog:
 *
 * 1. The cancellation asks for the AUDITED motive: it is mandatory, because it
 *    revokes nominative rights that were already delivered.
 * 2. The dialog states that the operation is NOT a monetary refund: it
 *    cancels the purchase and revokes the rights, it never returns money.
 *
 * The component handles ZERO raw error logic: the failures travel through
 * `handleApiError` inside the service and reach the administrator through the
 * alert of the dialog and the toast adapter.
 */

/** Fields of the cancellation. */
const CAMPOS_MOTIVO: FormField[] = [
  {
    name: "motivo",
    label: "Motivo de la cancelación",
    type: "textarea",
    required: true,
    maxLength: 1000,
    helperText: "Queda registrado como parte de la auditoría.",
    containerClassName: "col-span-12",
  },
];

/**
 * AdminPaseCampo — ONE field of the dialog.
 *
 * The field is rendered with the shared `GenericInput`, so the label, the
 * helper text and the error message are the shared ones of the application.
 * The state comes from the context of `GenericForm`: the component NEVER
 * owns a value and NEVER validates by itself (`contract/smart.md` §2).
 */
function AdminPaseCampo({ campo }: { campo: FormField }) {
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
        <AdminPaseCampo key={campo.name} campo={campo} />
      ))}
    </div>
  );
}

export interface AdminPaseCancelarDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** The purchase that is cancelled. */
  compraId: string;
  /** The payment order of the purchase — `null` when it has none. */
  ordenPagoId?: string | null;
  /** Commercial name of the purchased pass. */
  productoNombre?: string | null;
  /** Number of passes of the batch. */
  cantidad?: number | null;
  /** Active rights that the cancellation will revoke. */
  beneficiariosActivos?: number | null;
}

export function AdminPaseCancelarDialog({
  open,
  onOpenChange,
  compraId,
  ordenPagoId,
  productoNombre,
  cantidad,
  beneficiariosActivos,
}: AdminPaseCancelarDialogProps) {
  const formId = useId();
  const cancelar = useCancelarCompraPase();

  return (
    <GenericModal
      open={open}
      onOpenChange={onOpenChange}
      preventClose={cancelar.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title="Cancelar la compra de pases"
          description="La cancelación revoca los pases ya entregados y queda auditada."
        />

        <GenericModal.Body className="space-y-4">
          <dl
            aria-label="Compra de pases"
            className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <dt className="font-black uppercase tracking-wider text-slate-500">
                Producto
              </dt>
              <dd className="font-bold text-slate-800">
                {productoNombre ?? "Pase de fiesta"}
              </dd>
            </div>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <dt className="font-black uppercase tracking-wider text-slate-500">
                Pases
              </dt>
              <dd className="font-bold text-slate-800">{cantidad ?? "—"}</dd>
            </div>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <dt className="font-black uppercase tracking-wider text-slate-500">
                Derechos activos
              </dt>
              <dd className="font-bold text-slate-800">
                {beneficiariosActivos ?? 0}
              </dd>
            </div>
          </dl>

          <div
            role="alert"
            className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900"
          >
            <TriangleAlert
              className="mt-0.5 size-5 shrink-0"
              aria-hidden="true"
            />
            <p>{adminPaseCancelacionAviso()}</p>
          </div>

          <GenericForm
            formId={formId}
            schema={AdminPaseCancelarFormSchema}
            fields={CAMPOS_MOTIVO}
            initialData={{ motivo: "" }}
            onSubmit={async (datos) => {
              await cancelar.mutateAsync({
                compraId,
                ordenPagoId,
                motivo: datos.motivo,
              });
              onOpenChange(false);
            }}
            isLoading={cancelar.isPending}
            skipFooter
          >
            {() => <Campos campos={CAMPOS_MOTIVO} />}
          </GenericForm>

          {cancelar.error ? (
            <p role="alert" className="text-xs font-medium text-destructive">
              {cancelar.error.message}
            </p>
          ) : null}
        </GenericModal.Body>

        <GenericModal.Footer>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={cancelar.isPending}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form={formId}
            variant="destructive"
            disabled={cancelar.isPending}
          >
            {cancelar.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            Cancelar la compra de pases
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}
