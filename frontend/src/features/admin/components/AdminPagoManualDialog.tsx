"use client";

import { Loader2 } from "lucide-react";
import { useId } from "react";
import { useFormContext } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { GenericInput, type FormField } from "@/components/genericForm/GenericInput";
import { GenericModal } from "@/components/genericModal/GenericModal";
import { Button } from "@/components/ui/button";
import { notify } from "@/errors";
import {
  useAnularPagoManual,
  useAprobarPagoManual,
} from "../hooks/useAdminPagosComandos";
import {
  ADMIN_CANAL_PAGO_MANUAL,
  AdminPagoAnularManualFormSchema,
  AdminPagoAprobarManualFormSchema,
} from "../schemas";
import { canalPagoManualLabel } from "../utils/admin.estado.utils";

/**
 * AdminPagoManualDialog — the administrative approval and annulment of a
 * payment received outside the payment provider.
 *
 * Two decisions of this dialog:
 *
 * 1. The APPROVAL asks for the EVIDENCE (channel, reference, amount,
 *    currency, motive). The amount and the currency are prefilled with the
 *    ORDER amounts: the approval never adjusts the price of an order, so the
 *    backend refuses any mismatch with 409 `MONTO_NO_COINCIDE`.
 * 2. The ANNULMENT asks only for the audited motive: it is not a monetary
 *    refund, it revokes the rights that the approval funded.
 *
 * The component handles ZERO raw error logic: the failures travel through
 * `handleApiError` inside the service and reach the administrator through
 * the alert of the dialog and the toast adapter.
 */

/** Fields of the approval of a manual payment. */
const CAMPOS_APROBAR: FormField[] = [
  {
    name: "canal",
    label: "Canal del pago",
    type: "select",
    required: true,
    options: ADMIN_CANAL_PAGO_MANUAL.map((canal) => ({
      value: canal,
      label: canalPagoManualLabel(canal),
    })),
    helperText: "El canal forma parte de la evidencia de la aprobación.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "referencia",
    label: "Referencia del pago",
    type: "text",
    required: true,
    maxLength: 100,
    placeholder: "OP-123",
    helperText: "El identificador del abono verificado.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "monto",
    label: "Monto",
    type: "text",
    required: true,
    inputMode: "numeric",
    helperText: "Debe coincidir exactamente con el monto de la orden.",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "moneda",
    label: "Moneda",
    type: "text",
    required: true,
    maxLength: 3,
    placeholder: "PEN",
    containerClassName: "col-span-12 md:col-span-6",
  },
  {
    name: "motivo",
    label: "Motivo de la aprobación",
    type: "textarea",
    required: true,
    maxLength: 1000,
    helperText: "Queda registrado como parte de la auditoría.",
    containerClassName: "col-span-12",
  },
];

/** Fields of the annulment of a manual approval. */
const CAMPOS_ANULAR: FormField[] = [
  {
    name: "motivo",
    label: "Motivo de la anulación",
    type: "textarea",
    required: true,
    maxLength: 1000,
    helperText:
      "La anulación revoca los derechos financiados; no es un reembolso.",
    containerClassName: "col-span-12",
  },
];

export type AdminPagoManualModo = "aprobar" | "anular";

export interface AdminPagoManualDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** The state of the dialog. */
  onOpenChange: (open: boolean) => void;
  /** Whether the dialog approves a payment or annuls an approval. */
  modo: AdminPagoManualModo;
  /** Identifier of the payment order. */
  ordenPagoId: string;
  /** Human readable number of the order. */
  numeroOrden?: string | null;
  /** Amount of the order, prefilled in the approval. */
  montoOrden?: number | null;
  /** Currency of the order, prefilled in the approval. */
  monedaOrden?: string | null;
}

/**
 * AdminPagoCampo — ONE field of the dialog.
 *
 * The field is rendered with the shared `GenericInput`, so the label, the
 * helper text and the error message are the shared ones of the application.
 * The state comes from the context of `GenericForm`: the component NEVER
 * owns a value and NEVER validates by itself (`contract/smart.md` §2).
 */
function AdminPagoCampo({ campo }: { campo: FormField }) {
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
        <AdminPagoCampo key={campo.name} campo={campo} />
      ))}
    </div>
  );
}

/**
 * AdminPagoManualDialog — approve or annul a manual payment.
 */
export function AdminPagoManualDialog({
  open,
  onOpenChange,
  modo,
  ordenPagoId,
  numeroOrden,
  montoOrden,
  monedaOrden,
}: AdminPagoManualDialogProps) {
  const formId = useId();
  const aprobar = useAprobarPagoManual();
  const anular = useAnularPagoManual();
  const esAprobar = modo === "aprobar";
  const mutacion = esAprobar ? aprobar : anular;

  const montoInicial =
    montoOrden === null || montoOrden === undefined ? "" : String(montoOrden);

  return (
    <GenericModal
      open={open}
      onOpenChange={onOpenChange}
      preventClose={mutacion.isPending}
    >
      <GenericModal.Content>
        <GenericModal.Header
          title={
            esAprobar
              ? "Registrar el pago manual"
              : "Anular la aprobación del pago"
          }
          description={
            esAprobar
              ? "El monto y la moneda deben coincidir con la orden. La aprobación queda auditada."
              : "La anulación revoca los derechos financiados por la compra y conserva la auditoría."
          }
        />

        <GenericModal.Body className="space-y-4">
          <dl
            aria-label="Orden de pago"
            className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <dt className="font-black uppercase tracking-wider text-slate-500">
                Orden
              </dt>
              <dd className="font-bold text-slate-800">{numeroOrden ?? "—"}</dd>
            </div>
            {esAprobar ? (
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <dt className="font-black uppercase tracking-wider text-slate-500">
                  Monto de la orden
                </dt>
                <dd className="font-bold text-slate-800">
                  {montoInicial || "—"} {monedaOrden ?? "PEN"}
                </dd>
              </div>
            ) : null}
          </dl>

          {esAprobar ? (
            <GenericForm
              formId={formId}
              schema={AdminPagoAprobarManualFormSchema}
              fields={CAMPOS_APROBAR}
              initialData={{
                canal: "TRANSFERENCIA_BANCARIA" as const,
                referencia: "",
                monto: montoInicial,
                moneda: monedaOrden ?? "PEN",
                motivo: "",
              }}
              onSubmit={async (datos) => {
                aprobar.reset();
                await aprobar.mutateAsync({ ordenPagoId, datos });
                notify.success("El pago manual se registró correctamente.");
                onOpenChange(false);
              }}
              isLoading={aprobar.isPending}
              skipFooter
            >
              {() => <Campos campos={CAMPOS_APROBAR} />}
            </GenericForm>
          ) : (
            <GenericForm
              formId={formId}
              schema={AdminPagoAnularManualFormSchema}
              fields={CAMPOS_ANULAR}
              initialData={{ motivo: "" }}
              onSubmit={async (datos) => {
                anular.reset();
                await anular.mutateAsync({ ordenPagoId, datos });
                notify.success(
                  "La aprobación manual del pago se anuló correctamente.",
                );
                onOpenChange(false);
              }}
              isLoading={anular.isPending}
              skipFooter
            >
              {() => <Campos campos={CAMPOS_ANULAR} />}
            </GenericForm>
          )}

          {mutacion.error ? (
            <p role="alert" className="text-xs font-medium text-destructive">
              {mutacion.error.message}
            </p>
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
          <Button type="submit" form={formId} disabled={mutacion.isPending}>
            {mutacion.isPending ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : null}
            {esAprobar ? "Registrar el pago" : "Anular la aprobación"}
          </Button>
        </GenericModal.Footer>
      </GenericModal.Content>
    </GenericModal>
  );
}
