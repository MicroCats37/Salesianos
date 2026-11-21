"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Mail, Receipt, ShoppingBag, Ticket } from "lucide-react";
import { useEffect } from "react";
import type { Resolver, UseFormReturn } from "react-hook-form";
import { useController, useForm, useWatch } from "react-hook-form";
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
  useComprarPaseCliente,
  useComprarPedidoCliente,
} from "../hooks/useAsistidoAdmin";
import { useCotizacionPase } from "../hooks/useCotizacionPase";
import {
  type CompraParaClienteFormData,
  compraParaClienteFormSchema,
} from "../schemas/asistido.schema";
import {
  erroresDeCampoDeLaCompra,
  esPrecioCambiado,
} from "../utils/asistido.errores.utils";
import { BloqueIdentidadAdministrativa } from "./BloqueIdentidadAdministrativa";

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
   *
   * In the path of the PASSES it is NOT the price of the purchase: the
   * authoritative price is the one the QUOTATION publishes, and the quotation
   * is what the form shows.
   */
  precioUnitario?: string;
  /** The currency of the published price. */
  moneda?: string;
  /** Called when the command succeeded and the modal can close. */
  onComprado?: () => void;
}

const valoresIniciales: CompraParaClienteFormData = {
  tipo_documento: "DNI",
  numero_documento: "",
  nombres: "",
  apellidos: "",
  genero: "",
  estado_identidad: "SIN_CONSULTAR",
  contacto_email: "",
  cantidad: 1,
  canal: "EFECTIVO",
  referencia: "",
  motivo: "",
  monto_declarado: "",
};

/**
 * The quantity of the form, as the NUMBER the command travels.
 *
 * The control is a number and the form reads a string, so the value is
 * parsed and NOT calculated: a value that is not a positive integer has no
 * quotation at all.
 */
function cantidadValida(valor: unknown): number | null {
  const numero = typeof valor === "number" ? valor : Number(valor);

  if (!Number.isInteger(numero) || numero < 1) return null;

  return numero;
}

/**
 * Whether the server published a quotation of ZERO.
 *
 * The total arrives as TEXT: it is compared, never calculated. A total of
 * zero is NOT a paid purchase: the pass has no price and it belongs to the
 * path of the COURTESY, not to this one.
 */
function esTotalEnCero(total: string): boolean {
  return /^0(\.0+)?$/.test(total.trim());
}

/**
 * ModalCompraParaCliente - the assisted purchase for a third party.
 *
 * ## WHO BUYS
 *
 * The form declares the CIVIL identity of the CLIENT: type of document,
 * number, and —only when the padrón does not have that person— the names,
 * the surname and the gender. The backend resolves that identity in the
 * padrón (registering it if it did not exist, NEVER as an account) and makes
 * the CLIENT the owner of the purchase. The administrator who fills this
 * form is the ACTOR of the operation, not its buyer.
 *
 * ## WHAT IT COSTS
 *
 * The form NEVER sends a price and NEVER sends a total: the browser never
 * multiplies a price by a quantity (`RN-C02`). In the path of the PASSES the
 * server publishes a QUOTATION with the unit price, the total and the
 * currency, and the form shows them as they arrive.
 *
 * The price may move while the form is open: the quotation publishes the
 * token of the price it read, the command travels with that token and the
 * server answers `409 PRECIO_CAMBIADO` when the price moved. The form then
 * asks for a NEW quotation instead of retrying blindly.
 *
 * ## THE DECLARED AMOUNT
 *
 * The administrator may declare the amount he received. It is INFORMATIVE
 * and AUDITED evidence: it never becomes the price, the total, the state of
 * the payment nor the state of the purchase. The server confirms the total.
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
  onComprado,
}: ModalCompraParaClienteProps) {
  const esPase = modo === "PASE";
  const comprarPase = useComprarPaseCliente();
  const comprarPedido = useComprarPedidoCliente();
  const comprando = esPase ? comprarPase.isPending : comprarPedido.isPending;

  /**
   * The methods live HERE and not inside the `GenericForm`.
   *
   * The form owns them because it has to reach the controls when the server
   * answers a `422`: the error of each field reaches the control that owns
   * it, and the quotation has to be invalidated when the price moved.
   */
  const methods = useForm<CompraParaClienteFormData>({
    resolver: zodResolver(
      compraParaClienteFormSchema,
    ) as Resolver<CompraParaClienteFormData>,
    defaultValues: valoresIniciales,
  });

  const {
    cotizacion,
    estaCotizando,
    fallo: falloCotizacion,
    cotizar,
    invalidar,
  } = useCotizacionPase();

  /**
   * ONLY the quantity is watched: it is the one value that decides WHICH
   * quotation the form is showing.
   */
  const cantidad = useWatch({ control: methods.control, name: "cantidad" });
  const cantidadNumerica = cantidadValida(cantidad);

  /**
   * The quotation belongs to ONE pass AND ONE quantity.
   *
   * When the quantity changes, the previous quotation is dropped and a new
   * one is asked for: showing the old total would be showing a price of
   * another purchase.
   */
  useEffect(() => {
    if (!esPase || !open) return;

    invalidar();

    if (cantidadNumerica === null) return;

    cotizar(itemId, cantidadNumerica);
  }, [cantidadNumerica, cotizar, esPase, invalidar, itemId, open]);

  /**
   * The quotation that matches the quantity that is on the screen.
   *
   * `null` means there is NO price to show and NO command to send: the
   * button stays disabled until the server publishes one.
   */
  const cotizacionVigente =
    esPase &&
    cotizacion !== null &&
    cantidadNumerica !== null &&
    cotizacion.cantidad === cantidadNumerica
      ? cotizacion
      : null;

  const totalEnCero =
    cotizacionVigente !== null && esTotalEnCero(cotizacionVigente.total);

  async function alEnviar(datos: CompraParaClienteFormData) {
    const cliente = {
      tipo_documento: datos.tipo_documento,
      numero_documento: datos.numero_documento,
      nombres: datos.nombres,
      apellidos: datos.apellidos,
      genero: datos.genero,
      contacto_email: datos.contacto_email,
    };

    if (!esPase) {
      await comprarPedido.mutateAsync({
        items: [
          {
            tipo: "PRODUCTO",
            producto_id: itemId,
            cantidad: datos.cantidad,
          },
        ],
        cliente,
        evidencia: {
          canal: datos.canal,
          referencia: datos.referencia,
          motivo: datos.motivo,
        },
      });

      onComprado?.();
      return;
    }

    const montoDeclarado = datos.monto_declarado.trim();

    try {
      await comprarPase.mutateAsync({
        pase_id: itemId,
        cantidad: datos.cantidad,
        cliente,
        evidencia: {
          canal: datos.canal,
          referencia: datos.referencia,
          motivo: datos.motivo,
          ...(montoDeclarado ? { monto_declarado: montoDeclarado } : {}),
          ...(cotizacionVigente
            ? { precio_version: cotizacionVigente.version }
            : {}),
        },
      });

      onComprado?.();
    } catch (error) {
      /**
       * The price moved since the quotation: the quotation that the form is
       * showing belongs to a price that no longer exists. It is dropped and
       * asked again, and the command is NOT retried blindly.
       */
      if (esPrecioCambiado(error)) {
        invalidar();
        cotizar(itemId, datos.cantidad);
      }

      /**
       * The `422` of the server reaches the control that owns the field.
       */
      for (const [campo, mensaje] of Object.entries(
        erroresDeCampoDeLaCompra(error),
      )) {
        methods.setError(campo as keyof CompraParaClienteFormData, {
          message: mensaje,
        });
      }

      throw error;
    }
  }

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
      primaryDisabled={esPase && (cotizacionVigente === null || totalEnCero)}
      onPrimary={() => undefined}
      schema={compraParaClienteFormSchema}
      initialData={valoresIniciales}
      formMethods={methods}
      onSubmit={alEnviar}
      showErrorsAsToasts
      size="xl"
      bodyClassName="max-h-[70vh] overflow-y-auto"
      formClassName="flex flex-col gap-4"
    >
      {({ isSubmitting, submissionMessage }) => (
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

            {esPase ? (
              <CotizacionDelPase
                cotizacion={cotizacionVigente}
                estaCotizando={estaCotizando}
                fallo={falloCotizacion}
                totalEnCero={totalEnCero}
              />
            ) : precioUnitario ? (
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

          <CamposCompraCliente
            methods={methods}
            bloqueado={isSubmitting}
            esPase={esPase}
          />
        </>
      )}
    </AppFormModal>
  );
}

/**
 * The QUOTATION of the pass, exactly as the server published it.
 *
 * Every amount is printed as it arrived: the browser never multiplies a
 * price by a quantity and never formats an amount of its own.
 *
 * ## THE LIVE REGION
 *
 * The quotation arrives ASYNCHRONOUSLY: the operator changes the quantity
 * and the price is read from the server a moment later. The status and the
 * amounts live in a POLITE live region so a screen reader announces that the
 * price is being read and, when it lands, that the TOTAL changed — that
 * total is the whole point of the command.
 *
 * The region is BUSY while the request travels: the announcement waits for
 * the answer instead of reading an intermediate state.
 *
 * The FAILURE is not part of the region: it is an assertive `role="alert"`
 * of its own, so an error is never announced twice.
 */
function CotizacionDelPase({
  cotizacion,
  estaCotizando,
  fallo,
  totalEnCero,
}: {
  cotizacion: {
    cantidad: number;
    precio_unitario: string;
    total: string;
    moneda: string;
  } | null;
  estaCotizando: boolean;
  fallo: string | null;
  totalEnCero: boolean;
}) {
  if (fallo) {
    return (
      <p role="alert" className="text-caption text-destructive">
        No se pudo cotizar el pase: {fallo}
      </p>
    );
  }

  return (
    <div
      aria-live="polite"
      aria-busy={estaCotizando}
      className="flex flex-col gap-1"
    >
      {!cotizacion ? (
        <p className="text-caption text-muted-foreground">
          {estaCotizando
            ? "Cotizando el precio actual del pase en el servidor..."
            : "El precio unitario y el total los publica el servidor: todavía no hay una cotización vigente."}
        </p>
      ) : null}

      {cotizacion && totalEnCero ? (
        <p className="text-caption text-destructive">
          Este pase no tiene precio vigente: regístralo como cortesía, no como
          una compra pagada.
        </p>
      ) : null}

      {cotizacion && !totalEnCero ? (
        <>
          <p className="text-caption text-muted-foreground">
            Cantidad cotizada: {cotizacion.cantidad}
          </p>
          <p className="text-caption text-muted-foreground">
            Precio unitario: {cotizacion.precio_unitario} {cotizacion.moneda}
          </p>
          <p className="text-sm font-semibold text-foreground">
            Total cotizado: {cotizacion.total} {cotizacion.moneda}
          </p>
          <p className="text-caption text-muted-foreground">
            El total lo confirma el servidor al registrar la compra: el
            navegador no lo calcula.
          </p>
        </>
      ) : null}
    </div>
  );
}

/**
 * The fields of the assisted purchase.
 *
 * The form is the Mode 1 (`children`): the label, the icon and the error of
 * every field are drawn ONCE by `FormField`. The IDENTITY lives in the
 * SHARED BLOCK, so the participant and the two purchases resolve a document
 * the same way. The two selects read their value with `useController`,
 * ACOTADO a su campo.
 */
function CamposCompraCliente({
  methods,
  bloqueado,
  esPase,
}: {
  methods: UseFormReturn<CompraParaClienteFormData>;
  bloqueado: boolean;
  esPase: boolean;
}) {
  const {
    register,
    control: controlFormulario,
    formState: { errors },
  } = methods;

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

        <BloqueIdentidadAdministrativa
          idPrefijo="cliente"
          bloqueado={bloqueado}
        />

        <FormGrid>
          <FormField
            id="cliente-correo"
            label="Correo de contacto"
            icon={Mail}
            span={12}
            helper="Es un dato de contacto de la COMPRA: no habilita ningún derecho y no se guarda en la persona."
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
            helper="Cambiar la cantidad vuelve a cotizar el pase en el servidor."
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
                  id={control.id}
                  aria-invalid={control["aria-invalid"]}
                  aria-describedby={control["aria-describedby"]}
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

          {esPase ? (
            <FormField
              id="pago-monto-declarado"
              label="Importe declarado (informativo)"
              icon={Receipt}
              span={12}
              helper="El servidor confirma el total; este importe queda sólo como evidencia auditada."
              error={errors.monto_declarado?.message}
            >
              {(control) => (
                <Input
                  {...control}
                  {...register("monto_declarado")}
                  type="text"
                  inputMode="decimal"
                  placeholder="Por ejemplo, 35 o 35.50"
                />
              )}
            </FormField>
          ) : null}
        </FormGrid>
      </section>
    </fieldset>
  );
}
