"use client";

import { AlertCircle, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { notify } from "@/errors";
import { usePagoPedido } from "../hooks/usePedidoSeguimiento";
import type {
  IzipayConfirmacionPedido,
  IzipayPreparacionPedido,
} from "../schemas/pedido.schema";
import { obtenerEstadoTransaccionPedido } from "../services/marketplace.service";

interface IzipayCheckout {
  LoadForm(options: {
    authorization: string;
    keyRSA?: string;
    callbackResponse: (response: IzipayConfirmacionPedido) => void;
  }): void;
  Unmount?: () => void;
}

interface IzipayConstructor {
  new (options: { config: Record<string, unknown> }): IzipayCheckout;
}

declare global {
  interface Window {
    Izipay?: IzipayConstructor;
  }
}

type Fase = "preparando" | "abierto" | "recuperando" | "error";

const INTERVALO_SONDEO_MS = 2_000;
const MAX_SONDEOS = 15;
const PERIODO_GRACIA_MS = 1_500;

async function esperarSdkIzipay() {
  if (window.Izipay) return true;
  for (let intento = 0; intento < 30; intento += 1) {
    await new Promise((resolve) => setTimeout(resolve, 100));
    if (window.Izipay) return true;
  }
  return false;
}

function direccionComprador(preparacion: IzipayPreparacionPedido) {
  return {
    firstName: preparacion.buyer_name || "Cliente",
    lastName: preparacion.buyer_surname || "Invitado",
    email: preparacion.buyer_email || "pagos@salesianos.pe",
    phoneNumber: "999999999",
    street: "Av. Arequipa 123",
    city: "Lima",
    state: "Lima",
    country: "PE",
    postalCode: "00001",
    documentType: "DNI",
    document: "00000000",
  };
}

export interface IzipayPedidoModalProps {
  abierto: boolean;
  token: string;
  onCerrar: () => void;
  onEstadoActualizado: () => Promise<unknown>;
}

export function IzipayPedidoModal({
  abierto,
  token,
  onCerrar,
  onEstadoActualizado,
}: IzipayPedidoModalProps) {
  const { prepararPago, confirmarPago } = usePagoPedido(token);
  const [fase, setFase] = useState<Fase>("preparando");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const checkoutRef = useRef<IzipayCheckout | null>(null);
  const launchedRef = useRef(false);
  const relayedRef = useRef(false);
  const relayResueltoRef = useRef(false);
  const observerRef = useRef<MutationObserver | null>(null);
  const graciaRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const teardownCheckout = useCallback(() => {
    observerRef.current?.disconnect();
    observerRef.current = null;
    if (graciaRef.current) clearTimeout(graciaRef.current);
    graciaRef.current = null;
    try {
      checkoutRef.current?.Unmount?.();
    } catch {
      // A provider teardown failure must not block the checkout cleanup.
    }
    checkoutRef.current = null;
  }, []);

  const refrescarYcerrar = useCallback(async () => {
    try {
      await onEstadoActualizado();
    } catch {
      // The tracking page reads the authoritative state on the next visit.
    }
    onCerrar();
  }, [onCerrar, onEstadoActualizado]);

  const iniciarRecuperacion = useCallback(
    async (transactionId: string) => {
      setFase("recuperando");
      for (
        let intento = 0;
        intento < MAX_SONDEOS && !relayResueltoRef.current;
        intento += 1
      ) {
        try {
          const transaccion = await obtenerEstadoTransaccionPedido(
            token,
            transactionId,
          );
          if (transaccion.status === "EXITO") {
            notify.success("Pago confirmado. Actualizando tu pedido...");
            await refrescarYcerrar();
            return;
          }
          if (["FALLIDO", "CANCELADO"].includes(transaccion.status)) {
            setMensaje(
              transaccion.response_message ||
                "El pago no fue aprobado por Izipay.",
            );
            setFase("error");
            return;
          }
        } catch {
          // A failed read does not prove that the provider payment failed.
        }
        await new Promise((resolve) =>
          setTimeout(resolve, INTERVALO_SONDEO_MS),
        );
      }
      if (!relayResueltoRef.current) {
        setMensaje(
          "No pudimos verificar el pago todavía. Revisa el pedido en unos minutos.",
        );
        setFase("error");
      }
    },
    [refrescarYcerrar, token],
  );

  const abrirCheckout = useCallback(async () => {
    if (launchedRef.current) return;
    launchedRef.current = true;
    setFase("preparando");
    setMensaje(null);

    try {
      const preparacion = await prepararPago();
      if (!(await esperarSdkIzipay()) || !window.Izipay) {
        setMensaje("El SDK de Izipay no se ha cargado correctamente.");
        setFase("error");
        return;
      }

      const config = {
        action: "pay",
        merchantCode: preparacion.merchant_code,
        transactionId: preparacion.transaction_id,
        order: {
          orderNumber: preparacion.order_number,
          currency: preparacion.currency || "PEN",
          amount: Number(preparacion.amount).toFixed(2),
          processType: "AT",
          payMethod: "CARD,QR,YAPE_CODE,PAGO_PUSH",
          merchantBuyerId: preparacion.buyer_email || "00000000",
          dateTimeTransaction: String(Date.now() * 1000),
        },
        billing: direccionComprador(preparacion),
        shipping: direccionComprador(preparacion),
        render: {
          typeForm: "pop-up",
          container: "#izipay-checkout",
          showButtonProcessForm: true,
        },
        language: "es",
        originEntry: "WEB",
      };

      const checkout = new window.Izipay({ config });
      checkoutRef.current = checkout;

      // Literal legacy relay: the SDK callback is forwarded once as kr_answer.
      const callbackResponsePayment = async (
        providerPayload: IzipayConfirmacionPedido,
      ) => {
        if (relayedRef.current) return;
        relayedRef.current = true;
        observerRef.current?.disconnect();
        observerRef.current = null;

        if (providerPayload.code !== "00") {
          relayResueltoRef.current = true;
          notify.error(
            providerPayload.message || "El pago no fue aprobado por Izipay.",
          );
          onCerrar();
          return;
        }

        try {
          await confirmarPago(providerPayload);
          relayResueltoRef.current = true;
          notify.success("Pago realizado con éxito.");
          await refrescarYcerrar();
        } catch {
          void iniciarRecuperacion(preparacion.transaction_id);
        }
      };

      checkout.LoadForm({
        authorization: preparacion.token,
        keyRSA: "RSA",
        callbackResponse: callbackResponsePayment,
      });
      setFase("abierto");

      const container = document.getElementById("izipay-checkout");
      if (container) {
        observerRef.current = new MutationObserver(() => {
          if (
            container.childElementCount !== 0 ||
            relayedRef.current ||
            graciaRef.current
          )
            return;
          graciaRef.current = setTimeout(() => {
            graciaRef.current = null;
            if (!relayedRef.current)
              void iniciarRecuperacion(preparacion.transaction_id);
          }, PERIODO_GRACIA_MS);
        });
        observerRef.current.observe(container, {
          childList: true,
          subtree: true,
        });
      }
    } catch {
      setMensaje("No pudimos iniciar el pago. Inténtalo nuevamente.");
      setFase("error");
    }
  }, [
    confirmarPago,
    iniciarRecuperacion,
    onCerrar,
    prepararPago,
    refrescarYcerrar,
  ]);

  useEffect(() => {
    if (abierto) void abrirCheckout();
  }, [abierto, abrirCheckout]);

  useEffect(() => {
    if (!abierto) {
      launchedRef.current = false;
      relayedRef.current = false;
      relayResueltoRef.current = false;
      teardownCheckout();
      setFase("preparando");
      setMensaje(null);
    }
  }, [abierto, teardownCheckout]);

  useEffect(() => teardownCheckout, [teardownCheckout]);

  return (
    <Dialog open={abierto} onOpenChange={(open) => !open && onCerrar()}>
      <DialogContent
        className="sm:max-w-[400px] border-none bg-transparent p-0 shadow-none"
        showCloseButton={false}
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Pasarela de Pago Izipay</DialogTitle>
        </DialogHeader>
        {fase === "preparando" || fase === "recuperando" ? (
          <div className="flex flex-col items-center justify-center gap-4 rounded-[32px] bg-surface-raised p-8 shadow-2xl">
            <Loader2
              className="size-6 animate-spin text-primary"
              aria-hidden="true"
            />
            <p className="text-eyebrow-brand text-muted-foreground">
              {fase === "preparando"
                ? "Iniciando pasarela..."
                : "Verificando el pago..."}
            </p>
          </div>
        ) : null}
        {fase === "error" ? (
          <div
            role="alert"
            className="flex flex-col items-center justify-center gap-4 rounded-[32px] bg-surface-raised p-8 shadow-2xl"
          >
            <AlertCircle
              className="size-6 text-destructive"
              aria-hidden="true"
            />
            <p className="text-center text-sm font-semibold text-foreground">
              {mensaje}
            </p>
            <Button variant="outline" onClick={onCerrar} className="min-h-11">
              Cerrar
            </Button>
          </div>
        ) : null}
        <div id="izipay-checkout" className="w-full" />
      </DialogContent>
    </Dialog>
  );
}
