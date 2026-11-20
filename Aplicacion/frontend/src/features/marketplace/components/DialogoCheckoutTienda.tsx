"use client";

import { TriangleAlert } from "lucide-react";
import { useState } from "react";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { handleApiError, notify } from "@/errors";
import type { CrearPedido } from "../schemas/pedido.schema";
import type {
  ProductoDetalle,
  VeredictoPago,
} from "../types/marketplace.types";
import { formatearMonto } from "../utils/monto";
import { EstadoPagoTienda } from "./EstadoPagoTienda";

export interface DialogoCheckoutTiendaProps {
  /** The product that is being bought. */
  producto: ProductoDetalle;
  /** The amount of units. */
  cantidad: number;
  /** Whether the dialog is open. */
  abierto: boolean;
  /** The change of the open state. */
  onOpenChange: (abierto: boolean) => void;
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /** The currency of the price, when the edition publishes one. */
  moneda?: string;
  /** Creates the order with the guest identity captured here. */
  crearPedido: (comprador: Omit<CrearPedido, "items">) => Promise<void>;
}

/** The fields of the guest identity. */
type Campo = keyof Omit<CrearPedido, "items">;

type Errores = Partial<Record<Campo, string>>;

const TIPOS_DOCUMENTO = ["DNI", "CE", "PAS"] as const;

/**
 * The check of the identity of the guest.
 *
 * It says what the CONTRACT of the order asks for and nothing more: the
 * document type is one of the three the server declares, the document number
 * and the names are needed, and the surnames and the email are optional
 * (`PedidoItemIn` / `CrearPedidoIn`).
 *
 * The price, the stock and the amount are NOT checked here: they belong to
 * the server (`RN-C02`).
 */
function validarComprador(comprador: Omit<CrearPedido, "items">): Errores {
  const errores: Errores = {};

  if (!TIPOS_DOCUMENTO.includes(comprador.tipo_documento)) {
    errores.tipo_documento = "Elige un tipo de documento.";
  }

  if (!comprador.numero_documento.trim()) {
    errores.numero_documento = "Escribe el número de documento.";
  } else if (comprador.numero_documento.trim().length > 20) {
    errores.numero_documento = "El número de documento es demasiado largo.";
  }

  if (!comprador.nombres.trim()) {
    errores.nombres = "Escribe tus nombres.";
  }

  const correo = comprador.contacto_email.trim();
  if (correo && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
    errores.contacto_email = "Ese correo no tiene un formato válido.";
  }

  return errores;
}

/**
 * DialogoCheckoutTienda - the checkout of the store.
 *
 * It is the checkout of the STORE, and only of it: there is no mixed cart
 * between registrations, passes and store products (`GOV-02-RB-02a`).
 *
 * The identity is captured for guests, then resolved server-side into a
 * Persona without ever creating a Usuario account.
 *
 * **Closing the window never deletes the order** (`QA-C01`). The button is
 * named "Cerrar" and not "Cancelar el pedido".
 */
export function DialogoCheckoutTienda({
  producto,
  cantidad,
  abierto,
  onOpenChange,
  pago,
  moneda,
  crearPedido,
}: DialogoCheckoutTiendaProps) {
  const [fase, setFase] = useState<"inicial" | "enviando">("inicial");
  const [errores, setErrores] = useState<Errores>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [comprador, setComprador] = useState({
    tipo_documento: "DNI" as CrearPedido["tipo_documento"],
    numero_documento: "",
    nombres: "",
    apellidos: "",
    contacto_email: "",
  });

  function actualizar(campo: Campo, valor: string) {
    setComprador((actual) => {
      switch (campo) {
        case "tipo_documento":
          return {
            ...actual,
            tipo_documento: valor as CrearPedido["tipo_documento"],
          };
        case "numero_documento":
          return { ...actual, numero_documento: valor };
        case "nombres":
          return { ...actual, nombres: valor };
        case "apellidos":
          return { ...actual, apellidos: valor };
        case "contacto_email":
          return { ...actual, contacto_email: valor };
        default:
          return actual;
      }
    });
    setErrores((actual) => {
      if (!actual[campo]) return actual;
      const siguiente = { ...actual };
      delete siguiente[campo];
      return siguiente;
    });
  }

  async function alContinuar() {
    const fallos = validarComprador(comprador);
    setErrores(fallos);
    if (Object.keys(fallos).length > 0) {
      notify.error("Revisa los datos del comprador antes de continuar.");
      return;
    }

    setErrorGeneral(null);
    setFase("enviando");
    try {
      await crearPedido(comprador);
    } catch (error) {
      const mensaje = handleApiError(error).message;
      setErrorGeneral(mensaje);
      notify.error(mensaje);
    } finally {
      setFase("inicial");
    }
  }

  return (
    <Dialog open={abierto} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Compra como invitado</DialogTitle>
          <DialogDescription>
            {`${cantidad} ${cantidad === 1 ? "unidad" : "unidades"} de ${producto.nombre}. El total lo confirma el servidor al crear el pedido, con el precio vigente en ese momento.`}
          </DialogDescription>
        </DialogHeader>

        {pago ? (
          <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
            <EstadoPagoTienda veredicto={pago} conDescripcion />
          </div>
        ) : null}

        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-0.5">
            <dt className="text-caption text-muted-foreground">Producto</dt>
            <dd className="text-sm font-semibold text-foreground">
              {producto.nombre}
            </dd>
          </div>
          <div className="flex flex-col gap-0.5">
            <dt className="text-caption text-muted-foreground">
              Precio unitario
            </dt>
            <dd className="text-sm font-semibold tabular-nums text-foreground">
              {formatearMonto(producto.precio_efectivo, moneda ?? "")}
            </dd>
          </div>
        </dl>

        <FormGrid>
          <FormField
            id="pedido-tipo-documento"
            label="Tipo de documento"
            required
            span={6}
            error={errores.tipo_documento}
          >
            {(control) => (
              <Input
                {...control}
                value={comprador.tipo_documento}
                onChange={(evento) =>
                  actualizar(
                    "tipo_documento",
                    evento.target.value as CrearPedido["tipo_documento"],
                  )
                }
              />
            )}
          </FormField>

          <FormField
            id="pedido-numero-documento"
            label="Número de documento"
            required
            span={6}
            error={errores.numero_documento}
          >
            {(control) => (
              <Input
                {...control}
                value={comprador.numero_documento}
                onChange={(evento) =>
                  actualizar("numero_documento", evento.target.value)
                }
              />
            )}
          </FormField>

          <FormField
            id="pedido-nombres"
            label="Nombres"
            required
            span={6}
            error={errores.nombres}
          >
            {(control) => (
              <Input
                {...control}
                value={comprador.nombres}
                onChange={(evento) =>
                  actualizar("nombres", evento.target.value)
                }
              />
            )}
          </FormField>

          <FormField
            id="pedido-apellidos"
            label="Apellidos"
            span={6}
            error={errores.apellidos}
          >
            {(control) => (
              <Input
                {...control}
                value={comprador.apellidos}
                onChange={(evento) =>
                  actualizar("apellidos", evento.target.value)
                }
              />
            )}
          </FormField>

          <FormField
            id="pedido-correo"
            label="Correo de contacto"
            span={12}
            helper="Opcional. Es donde llega el enlace de seguimiento del pedido."
            error={errores.contacto_email}
          >
            {(control) => (
              <Input
                {...control}
                type="email"
                inputMode="email"
                autoComplete="email"
                value={comprador.contacto_email}
                onChange={(evento) =>
                  actualizar("contacto_email", evento.target.value)
                }
              />
            )}
          </FormField>
        </FormGrid>

        {errorGeneral ? (
          <p
            role="alert"
            className="flex items-center gap-1.5 text-caption text-destructive"
          >
            <TriangleAlert className="size-3.5 shrink-0" aria-hidden="true" />
            {errorGeneral}
          </p>
        ) : null}

        <p className="text-caption text-muted-foreground">
          Si cierras esta ventana, el pedido no se borra: lo retomas con el
          enlace de seguimiento. Cerrar no cancela el pedido ni confirma el
          pago.
        </p>

        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline" className="min-h-11">
              Cerrar
            </Button>
          </DialogClose>
          <Button
            type="button"
            className="min-h-11"
            disabled={fase === "enviando"}
            onClick={() => {
              void alContinuar();
            }}
          >
            {fase === "enviando" ? "Creando el pedido" : "Continuar al pago"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
