"use client";

import {
  Fingerprint,
  Mail,
  Receipt,
  ShoppingBag,
  Ticket,
  User,
} from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { useController } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import {
  type CompraParaClienteFormData,
  compraParaClienteFormSchema,
} from "../schemas/asistido.schema";

/** What is being bought FOR the client. */
export type ModoCompraCliente = "PASE" | "PRODUCTO";

export interface ModalCompraParaClienteProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Called when the modal opens or closes. */
  onOpenChange: (open: boolean) => void;
  /** What is being bought: a pass of the catalogue or a product of the store. */
  modo: ModoCompraCliente;
  /** The name of the item, as the catalogue published it. */
  concepto: string;
  /** The identifier of the pass or the product. */
  itemId: string;
  /**
   * The price the CATALOGUE published.
   *
   * It is a published FACT, not a computation: the browser never multiplies
   * it by a quantity and never sends a total. The server freezes the total
   * of the purchase against the catalogue (`RN-C02`).
   */
  precioUnitario?: string;
  /** The currency of the published price. */
  moneda?: string;
  /** Whether the command is running. */
  comprando: boolean;
  /** The command itself. */
  onComprar: (datos: CompraParaClienteFormData) => Promise<unknown>;
}

const valoresIniciales: CompraParaClienteFormData = {
  tipo_documento: "DNI",
  numero_documento: "",
  nombres: "",
  apellidos: "",
  contacto_email: "",
  cantidad: 1,
  canal: "EFECTIVO",
  referencia: "",
  motivo: "",
};

/**
 * ModalCompraParaCliente - the assisted purchase for a third party.
 *
 * ## WHO BUYS
 *
 * The form declares the CIVIL identity of the CLIENT: type of document,
 * number, names and contact email. The backend resolves that identity in the
 * padrón (registering it if it did not exist) and makes the CLIENT the owner
 * of the purchase. The administrator who fills this form is the ACTOR of the
 * operation, not its buyer.
 *
 * ## WHAT IT COSTS
 *
 * The form NEVER sends a total: the server freezes it against the catalogue
 * (`RN-C02`). The price the catalogue published is shown as a fact.
 *
 * ## THE PAYMENT
 *
 * The evidence of the external payment (channel, reference and reason) is
 * part of the same command: the assisted purchase registers the payment with
 * the canonical manual approval of the backend.
 */
export function ModalCompraParaCliente({
  open,
  onOpenChange,
  modo,
  concepto,
  itemId,
  precioUnitario,
  moneda,
  comprando,
  onComprar,
}: ModalCompraParaClienteProps) {
  const esPase = modo === "PASE";

  return (
    <AppFormModal<CompraParaClienteFormData>
      open={open}
      onOpenChange={onOpenChange}
      title="Comprar para cliente"
      description={`La compra queda a nombre del cliente que declares. El administrador que la registra es el actor de la operación y queda en el acta de la auditoría.`}
      eyebrow={esPase ? "Pases de la fiesta" : "Tienda del FEST"}
      icon={
        esPase ? (
          <Ticket className="size-5" aria-hidden="true" />
        ) : (
          <ShoppingBag className="size-5" aria-hidden="true" />
        )
      }
      primaryLabel="Registrar la compra y su pago"
      primaryLoadingLabel="Registrando..."
      primaryLoading={comprando}
      onPrimary={() => undefined}
      schema={compraParaClienteFormSchema}
      initialData={valoresIniciales}
      onSubmit={onComprar}
      showErrorsAsToasts
      size="xl"
      bodyClassName="max-h-[70vh] overflow-y-auto"
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <>
          {submissionMessage?.type === "error" ? (
            <p
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
            >
              {submissionMessage.message}
            </p>
          ) : null}

          <section
            aria-labelledby="resumen-compra-cliente"
            className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border p-4"
          >
            <h3
              id="resumen-compra-cliente"
              className="text-sm font-semibold text-foreground"
            >
              Lo que se compra
            </h3>
            <p className="text-sm text-foreground">{concepto}</p>
            {precioUnitario ? (
              <p className="text-caption text-muted-foreground">
                Precio de catálogo: {precioUnitario} {moneda ?? ""}. El total lo
                confirma el servidor al registrar la compra.
              </p>
            ) : (
              <p className="text-caption text-muted-foreground">
                El precio y el total los confirma el servidor al registrar la
                compra.
              </p>
            )}
            <p className="text-caption text-muted-foreground">
              Identificador del catálogo: {itemId}
            </p>
          </section>

          <CamposCompraCliente methods={methods} bloqueado={isSubmitting} />
        </>
      )}
    </AppFormModal>
  );
}

/**
 * The fields of the assisted purchase.
 *
 * The form is the Mode 1 (`children`): the label, the icon and the error of
 * every field are drawn ONCE by `FormField`. The two selects read their value
 * with `useController`, ACOTADO a su campo.
 */
function CamposCompraCliente({
  methods,
  bloqueado,
}: {
  methods: UseFormReturn<CompraParaClienteFormData>;
  bloqueado: boolean;
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: tipoDocumento } = useController({
    control: controlFormulario,
    name: "tipo_documento",
  });
  const { field: canal } = useController({
    control: controlFormulario,
    name: "canal",
  });

  return (
    <fieldset disabled={bloqueado} className="contents">
      <section
        aria-labelledby="cliente-compra-titulo"
        className="flex flex-col gap-3"
      >
        <h3
          id="cliente-compra-titulo"
          className="text-sm font-semibold text-foreground"
        >
          Identidad del cliente
        </h3>

        <FormGrid>
          <FormField
            id="cliente-tipo-documento"
            label="Tipo de documento"
            required
            icon={Fingerprint}
            span={4}
            error={errors.tipo_documento?.message}
          >
            {(control) => (
              <Select
                value={tipoDocumento.value}
                onValueChange={tipoDocumento.onChange}
              >
                <SelectTrigger
                  {...control}
                  onBlur={tipoDocumento.onBlur}
                  className="w-full"
                >
                  <SelectValue placeholder="Elige el tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DNI">DNI</SelectItem>
                  <SelectItem value="CE">Carné de extranjería</SelectItem>
                  <SelectItem value="PAS">Pasaporte</SelectItem>
                </SelectContent>
              </Select>
            )}
          </FormField>

          <FormField
            id="cliente-numero-documento"
            label="Número de documento"
            required
            icon={Fingerprint}
            span={8}
            error={errors.numero_documento?.message}
          >
            {(control) => (
              <Input
                {...control}
                {...register("numero_documento")}
                autoFocus
                inputMode="text"
              />
            )}
          </FormField>

          <FormField
            id="cliente-nombres"
            label="Nombres"
            required
            icon={User}
            span={6}
            error={errors.nombres?.message}
          >
            {(control) => <Input {...control} {...register("nombres")} />}
          </FormField>

          <FormField
            id="cliente-apellidos"
            label="Apellidos"
            icon={User}
            span={6}
            error={errors.apellidos?.message}
          >
            {(control) => <Input {...control} {...register("apellidos")} />}
          </FormField>

          <FormField
            id="cliente-correo"
            label="Correo de contacto"
            icon={Mail}
            span={12}
            helper="Es un dato de contacto: no habilita ningún derecho."
            error={errors.contacto_email?.message}
          >
            {(control) => (
              <Input
                {...control}
                {...register("contacto_email")}
                type="email"
                autoComplete="email"
              />
            )}
          </FormField>

          <FormField
            id="compra-cantidad"
            label="Cantidad"
            required
            span={6}
            error={errors.cantidad?.message}
          >
            {(control) => (
              <Input
                {...control}
                {...register("cantidad")}
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
              />
            )}
          </FormField>
        </FormGrid>
      </section>

      <section
        aria-labelledby="evidencia-pago-titulo"
        className="flex flex-col gap-3"
      >
        <h3
          id="evidencia-pago-titulo"
          className="text-sm font-semibold text-foreground"
        >
          Evidencia del pago
        </h3>

        <FormGrid>
          <FormField
            id="pago-canal"
            label="Canal"
            required
            icon={Receipt}
            span={6}
            error={errors.canal?.message}
          >
            {(control) => (
              <Select value={canal.value} onValueChange={canal.onChange}>
                <SelectTrigger
                  {...control}
                  onBlur={canal.onBlur}
                  className="w-full"
                >
                  <SelectValue placeholder="Elige el canal" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EFECTIVO">Efectivo</SelectItem>
                  <SelectItem value="TRANSFERENCIA_BANCARIA">
                    Transferencia bancaria
                  </SelectItem>
                  <SelectItem value="YAPE">Yape</SelectItem>
                  <SelectItem value="PLIN">Plin</SelectItem>
                  <SelectItem value="OTRO">Otro</SelectItem>
                </SelectContent>
              </Select>
            )}
          </FormField>

          <FormField
            id="pago-referencia"
            label="Referencia"
            required
            icon={Receipt}
            span={6}
            helper="Número de operación, recibo o voucher del pago."
            error={errors.referencia?.message}
          >
            {(control) => <Input {...control} {...register("referencia")} />}
          </FormField>

          <FormField
            id="pago-motivo"
            label="Motivo"
            required
            span={12}
            helper="Queda registrado en el acta de la acción sensible."
            error={errors.motivo?.message}
          >
            {(control) => (
              <Textarea {...control} {...register("motivo")} rows={3} />
            )}
          </FormField>
        </FormGrid>
      </section>
    </fieldset>
  );
}
