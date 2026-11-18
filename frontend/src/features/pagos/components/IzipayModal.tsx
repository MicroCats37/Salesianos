"use client";

/**
 * IzipayModal — Izipay Web Core 2.0 popup for payment.
 *
 * Flow:
 * 1. Modal opens → calls backend POST /compras/{compraId}/iniciar-pago
 * 2. Backend returns session token + public config (no secrets)
 * 3. Waits for window.Izipay SDK to be ready (bounded polling)
 * 4. Builds SDK config and calls checkout.LoadForm()
 * 5. SDK opens popup; on callback (code === "00") → relays the provider payload
 *    ONCE to POST /pagos/izipay/confirmar
 * 6. The backend verifies the payment and owns the commercial settlement: it
 *    marks the purchase paid and allocates the rights. The browser never sends
 *    a commercial-confirmation request.
 * 7. When the relay is UNCERTAIN — the popup closed without a conclusive
 *    answer, or the relay request itself failed — the browser reads the state
 *    of the transaction it prepared (GET /pagos/transacciones/{id}) with a
 *    BOUNDED polling. The relay is never the only confirmation channel.
 * 8. On a verified payment → refresh the authoritative state (onSuccess) and
 *    close.
 *
 * Every failure the operator can act upon is rendered with the PUBLIC message
 * of the API (never a raw HTTP status string) and every closing of the modal
 * releases the provider checkout EXPLICITLY.
 */

import { AlertCircle, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { IzipayCallback } from "../schemas/pago.schema";
import {
  confirmarPagoIzipay,
  iniciarPagoIzipay,
  obtenerEstadoTransaccion,
} from "../services/pago.service";
import { observarCierreCheckout } from "../utils/checkout.observador";
import { sondearEstadoTransaccion } from "../utils/checkout.recuperacion";
import {
  type ErrorPreparacion,
  errorDeEnvoltura,
  errorDeExcepcion,
} from "../utils/preparacion.error";
import { settlementTone } from "../utils/settlement";

// ── Provider SDK contract ─────────────────────────────────────────────────────

/** Options of `checkout.LoadForm()` — opens the provider popup. */
interface IzipayLoadFormOptions {
  /** Session token of the popup — never a secret of ours. */
  authorization: string;
  /** Key exchange mode expected by the provider. */
  keyRSA?: string;
  /** Callback the provider invokes when the buyer closes the popup. */
  callbackResponse: (response: IzipayCallback) => void;
}

/** The checkout instance the provider SDK constructor returns. */
interface IzipayCheckout {
  /** Opens the payment form inside the container of the configuration. */
  LoadForm(options: IzipayLoadFormOptions): void;
  /** Releases the popup resources. */
  Unmount?: () => void;
}

/** Configuration the provider SDK receives to render the checkout. */
interface IzipayCheckoutConfig {
  /** Mandatory action of the Izipay Web Core 2.0 SDK contract. */
  action: "pay";
  /** Izipay Perú merchant/shop code. */
  merchantCode: string;
  /** 14-digit transaction id — the idempotency key of the payment. */
  transactionId: string;
  /** Order carried by the transaction. */
  order: {
    orderNumber: string;
    currency: string;
    amount: string;
    processType: string;
    payMethod: string;
    merchantBuyerId: string;
    dateTimeTransaction: string;
  };
  /** Billing data of the buyer. */
  billing: IzipayAddressData;
  /** Shipping data of the buyer. */
  shipping: IzipayAddressData;
  /** How the form is rendered. */
  render: {
    typeForm: string;
    container: string;
    showButtonProcessForm: boolean;
  };
  /** Language of the provider form. */
  language: string;
  /** Entry point of the session. */
  originEntry: string;
}

/** The provider SDK constructor exposed as `window.Izipay`. */
interface IzipayCheckoutConstructor {
  new (options: { config: IzipayCheckoutConfig }): IzipayCheckout;
}

declare global {
  interface Window {
    Izipay?: IzipayCheckoutConstructor;
  }
}

// ── SDK polling ────────────────────────────────────────────────────────────────

const SDK_POLL_INTERVAL_MS = 100;
const SDK_POLL_MAX_RETRIES = 30; // 3 seconds total

async function waitForIzipaySdk(): Promise<boolean> {
  if (window.Izipay) return true;
  for (let i = 0; i < SDK_POLL_MAX_RETRIES; i++) {
    await new Promise((r) => setTimeout(r, SDK_POLL_INTERVAL_MS));
    if (window.Izipay) return true;
  }
  return false;
}

// ── Amount normalization ───────────────────────────────────────────────────────

function normalizeAmount(value: unknown): string {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return "1.00";
  return n.toFixed(2);
}

// ── Text sanitizers ───────────────────────────────────────────────────────────

function sanitizeText(value: unknown): string {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function sanitizeNamePart(value: unknown, fallback: string): string {
  const cleaned = sanitizeText(value)
    .replace(/[^a-zA-Z\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const forbidden = ["ing", "dr", "dra", "sr", "sra", "test", "usuario"];
  if (!cleaned || forbidden.includes(cleaned.toLowerCase())) {
    return fallback;
  }
  return cleaned;
}

function sanitizePhone(value: unknown): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  return digits.length >= 7 ? digits.slice(0, 15) : "999999999";
}

function sanitizeDocument(value: unknown): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  return digits.length >= 8 ? digits.slice(0, 12) : "12345678";
}

function sanitizeEmail(value: unknown): string {
  const e = String(value ?? "").trim();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) ? e : "pagos@salesianos.pe";
}

/** Reads a provider field that is not part of the declared contract. */
function textoOpcional(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

// ── Buyer / address data for the SDK form ─────────────────────────────────────

interface IzipayAddressData {
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  street: string;
  city: string;
  state: string;
  country: string;
  postalCode: string;
  documentType: string;
  document: string;
}

function buildAddressData(raw: {
  firstName?: string | null;
  lastName?: string | null;
  email?: string | null;
  phoneNumber?: string | null;
  documentType?: string | null;
  document?: string | null;
}): IzipayAddressData {
  return {
    firstName: sanitizeNamePart(raw.firstName, "Juan"),
    lastName: sanitizeNamePart(raw.lastName, "Perez"),
    email: sanitizeEmail(raw.email),
    phoneNumber: sanitizePhone(raw.phoneNumber),
    street: "Av. Arequipa 123",
    city: "Lima",
    state: "Lima",
    country: "PE",
    postalCode: "00001",
    documentType: sanitizeText(raw.documentType) || "DNI",
    document: sanitizeDocument(raw.document),
  };
}

// ── Phases of the checkout ────────────────────────────────────────────────────

/**
 * State of the checkout inside the modal.
 *
 * - `preparando` — the backend is preparing the attempt.
 * - `abierto` — the provider popup is open.
 * - `recuperando` — the relay was uncertain: the state of the prepared
 *   transaction is being read.
 * - `error` — a typed failure the operator can act upon is rendered.
 */
type FaseCheckout = "preparando" | "abierto" | "recuperando" | "error";

/**
 * Grace period given to the provider callback before the checkout is
 * considered CLOSED without a relay.
 *
 * The provider releases what it rendered before it invokes the callback, so
 * the DOM signal arrives first. The grace period lets the callback win the
 * race: a checkout that was paid normally never enters the recovery.
 */
const PERIODO_GRACIA_MS = 1500;

// ── Props ──────────────────────────────────────────────────────────────────────

export interface IzipayModalProps {
  /** Controls modal visibility */
  isOpen: boolean;
  /** Called when modal should close (user dismissed or flow ended) */
  onClose: () => void;
  /** The pending purchase to pay for */
  compraId: string | null;
  /**
   * Called on confirmed payment success — the parent refreshes the
   * authoritative state (inscription detail, participant pool, cupo saldo).
   *
   * It may return a promise: the modal awaits it so the refreshed state is
   * already on screen when the modal closes.
   */
  onSuccess: () => void | Promise<void>;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function IzipayModal({
  isOpen,
  onClose,
  compraId,
  onSuccess,
}: IzipayModalProps) {
  const [fase, setFase] = useState<FaseCheckout>("preparando");
  const [errorPreparacion, setErrorPreparacion] =
    useState<ErrorPreparacion | null>(null);
  const checkoutRef = useRef<IzipayCheckout | null>(null);
  /**
   * One-shot guards. The checkout performs exactly two requests:
   * - `launchedRef` — one provider session per modal opening.
   * - `relayedRef` — one relay of the provider payload per session.
   * - `relayResueltoRef` — the relay reached a CONCLUSIVE answer, so the
   *   recovery of an uncertain relay must stop.
   */
  const launchedRef = useRef(false);
  const relayedRef = useRef(false);
  const relayResueltoRef = useRef(false);
  /** Stops the observer of the container of the checkout. */
  const observerRef = useRef<(() => void) | null>(null);
  /** Grace period pending — it must not survive the closing of the modal. */
  const graciaRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** Token of the recovery in flight — a newer token cancels the older one. */
  const recuperacionRef = useRef(0);

  /**
   * EXPLICIT teardown of the provider checkout.
   *
   * The popup owns resources: the session of the attempt and the DOM it
   * rendered. Closing the modal — or unmounting it — MUST release them, or a
   * stale checkout survives the flow it belonged to.
   */
  const teardownCheckout = useCallback(() => {
    observerRef.current?.();
    observerRef.current = null;

    // A grace period pending belongs to a checkout that no longer exists.
    if (graciaRef.current !== null) {
      clearTimeout(graciaRef.current);
      graciaRef.current = null;
    }

    const checkout = checkoutRef.current;
    checkoutRef.current = null;

    try {
      checkout?.Unmount?.();
    } catch {
      // A provider that fails to release itself must not break the flow.
    }
  }, []);

  /**
   * Recovers a payment whose relay was UNCERTAIN.
   *
   * It reads the state of the transaction THIS checkout prepared — the relay
   * cannot be the only confirmation channel. The polling is bounded and it
   * stops as soon as the relay resolves or the modal is closed.
   */
  const iniciarRecuperacion = useCallback(
    async (transactionId: string) => {
      const token = recuperacionRef.current + 1;
      recuperacionRef.current = token;

      setFase("recuperando");

      const resultado = await sondearEstadoTransaccion(
        transactionId,
        obtenerEstadoTransaccion,
        {
          cancelado: () =>
            recuperacionRef.current !== token || relayResueltoRef.current,
        },
      );

      // A newer recovery (or a closed modal) owns the outcome now.
      if (recuperacionRef.current !== token) return;

      if (resultado.estado === "exito") {
        toast.success("Pago confirmado. Actualizando tu inscripción...");
        try {
          await onSuccess();
        } catch {
          // The next navigation reads the authoritative state again.
        }
        onClose();
        return;
      }

      if (resultado.estado === "rechazado") {
        toast.error(resultado.mensaje || "El pago no fue aprobado por Izipay.");
        onClose();
        return;
      }

      if (resultado.estado === "cancelado") return;

      // The bound was reached without a conclusive answer: the payment is
      // NOT proven. The operator reads it and decides what to do next.
      setErrorPreparacion({
        code: null,
        message:
          "No se pudo verificar el pago. Revisa el estado de tu inscripción o inténtalo nuevamente.",
      });
      setFase("error");
    },
    [onSuccess, onClose],
  );

  const handleLaunchIzipay = useCallback(async () => {
    if (launchedRef.current || !compraId) return;
    launchedRef.current = true;
    setFase("preparando");
    setErrorPreparacion(null);

    try {
      // Step 1: Get session token from backend
      const prepareRes = await iniciarPagoIzipay(compraId);
      const prepareData = prepareRes.data;

      if (!prepareRes.success || !prepareData?.token) {
        // The envelope carries the TYPED error of the API: the operator reads
        // its public message, never a raw HTTP status string.
        setErrorPreparacion(
          errorDeEnvoltura(prepareRes.error) ?? {
            code: null,
            message: "No se pudo generar el token de pago.",
          },
        );
        setFase("error");
        return;
      }

      const d = prepareData;

      // Step 2: Wait for SDK global
      const sdkReady = await waitForIzipaySdk();
      if (!sdkReady || !window.Izipay) {
        setErrorPreparacion({
          code: null,
          message: "El SDK de Izipay no se ha cargado correctamente.",
        });
        setFase("error");
        return;
      }

      // Step 3: Build SDK config — all values come from the backend response
      const now = String(Date.now() * 1000);
      const amount = normalizeAmount(d.amount);
      const orderNumber = d.order_number;
      const transactionId = d.transaction_id;

      // The session token of the provider popup — never a secret of ours.
      const authorization = d.token;

      const finalConfig: IzipayCheckoutConfig = {
        action: "pay", // mandatory per Izipay Web Core 2.0 SDK contract
        merchantCode: d.merchant_code,
        transactionId,
        order: {
          orderNumber,
          currency: d.currency || "PEN",
          amount,
          processType: "AT",
          payMethod: "CARD,QR,YAPE_CODE,PAGO_PUSH",
          merchantBuyerId: d.buyer_email || "00000000",
          dateTimeTransaction: now,
        },
        billing: buildAddressData({
          firstName: d.buyer_name,
          lastName: d.buyer_surname,
          email: d.buyer_email,
          phoneNumber: "999999999",
          documentType: "DNI",
          document: "00000000",
        }),
        shipping: buildAddressData({
          firstName: d.buyer_name,
          lastName: d.buyer_surname,
          email: d.buyer_email,
          phoneNumber: "999999999",
          documentType: "DNI",
          document: "00000000",
        }),
        render: {
          typeForm: "pop-up",
          container: "#izipay-checkout",
          showButtonProcessForm: true,
        },
        language: "es",
        originEntry: "WEB",
      };

      // Step 4: Initialize checkout
      let checkout: IzipayCheckout;
      try {
        checkout = new window.Izipay({ config: finalConfig });
        checkoutRef.current = checkout;
      } catch (sdkInitError: unknown) {
        // Surface SDK validation errors without logging raw config
        const msg =
          sdkInitError instanceof Error
            ? sdkInitError.message
            : "Error al inicializar Izipay.";
        setErrorPreparacion({ code: null, message: msg });
        setFase("error");
        return;
      }

      // Step 5: Relay the provider payload — exactly once.
      const callbackResponsePayment = async (
        providerPayload: IzipayCallback,
      ) => {
        if (relayedRef.current) return;
        relayedRef.current = true;

        // The popup is gone: the observer of the container is not needed.
        observerRef.current?.();
        observerRef.current = null;

        const methodUsed =
          providerPayload.response?.payMethod ??
          textoOpcional(providerPayload.paymentMethod) ??
          "Izipay";

        if (providerPayload.code !== "00") {
          // A definitive rejection of the provider: there is nothing to poll.
          relayResueltoRef.current = true;
          toast.error(
            providerPayload.message || "El pago no fue aprobado por Izipay.",
          );
          onClose();
          return;
        }

        try {
          // The complete provider payload is relayed: the backend verifies the
          // provider signature over `payloadHttp` and cross-checks the
          // amount/order against the persisted transaction.
          const confirmRes = await confirmarPagoIzipay({
            kr_answer: providerPayload,
          });
          const confirm = confirmRes.data;

          if (!confirmRes.success || !confirm?.success) {
            relayResueltoRef.current = true;
            toast.error(
              confirmRes.error?.message ||
                confirm?.response_message ||
                "Error al confirmar el pago.",
            );
            onClose();
            return;
          }

          relayResueltoRef.current = true;

          // The backend owns the commercial settlement and reports whether the
          // purchase and its rights are already active. A pending settlement
          // must never be presented as a completed payment.
          if (settlementTone(confirm.settlement_status) === "completada") {
            toast.success(
              confirmRes.message ||
                `Pago con ${methodUsed} realizado con éxito.`,
            );
          } else {
            toast.warning(
              confirmRes.message ||
                "Pago confirmado. La activación comercial está pendiente.",
            );
          }
          // The payment is already recorded. The refresh of the authoritative
          // state is a separate concern: a failed refresh must never be
          // reported as a failed confirmation, and it must never leave the UI
          // showing a stale commercial state.
          try {
            await onSuccess();
          } catch {
            // The next navigation reads the authoritative state again.
          }
          onClose();
        } catch {
          // The relay FAILED: the payment may or may not have been recorded.
          // The relay is not the only confirmation channel → recover.
          toast.warning(
            `Pago con ${methodUsed} detectado. La confirmación no respondió; verificando el estado del pago...`,
          );
          void iniciarRecuperacion(d.transaction_id);
        }
      };

      // Step 6: Render the form (popup opens) — LoadForm is called on the checkout instance
      try {
        checkout.LoadForm({
          authorization,
          keyRSA: "RSA",
          callbackResponse: callbackResponsePayment,
        });
        setFase("abierto");
      } catch (sdkLoadError: unknown) {
        const msg =
          sdkLoadError instanceof Error
            ? sdkLoadError.message
            : "Error al abrir el formulario de pago.";
        setErrorPreparacion({ code: null, message: msg });
        setFase("error");
        return;
      }

      // Step 7: Watch the popup. When the provider STOPS rendering the
      // checkout and no relay arrived, the relay is UNCERTAIN: the browser
      // reads the state of the transaction it prepared.
      observerRef.current = observarCierreCheckout(
        document.getElementById("izipay-checkout"),
        () => {
          // The provider releases the DOM before it invokes the callback:
          // the grace period lets a normal relay win the race.
          graciaRef.current = setTimeout(() => {
            graciaRef.current = null;
            if (relayedRef.current) return;
            void iniciarRecuperacion(d.transaction_id);
          }, PERIODO_GRACIA_MS);
        },
      );
    } catch (err: unknown) {
      // The preparation failed with an HTTP error: the operator reads the
      // PUBLIC message of the API through the shared error handler.
      setErrorPreparacion(errorDeExcepcion(err));
      setFase("error");
    }
  }, [compraId, onClose, onSuccess, iniciarRecuperacion]);

  // Launch on open — exactly once per opening.
  useEffect(() => {
    if (isOpen && compraId) {
      void handleLaunchIzipay();
    }
  }, [isOpen, compraId, handleLaunchIzipay]);

  // Reset the one-shot guards when the modal closes so the next opening
  // performs a fresh checkout.
  useEffect(() => {
    if (!isOpen) {
      launchedRef.current = false;
      relayedRef.current = false;
      relayResueltoRef.current = false;
      // A recovery in flight does not survive the closing of the modal.
      recuperacionRef.current += 1;
      setFase("preparando");
      setErrorPreparacion(null);
    }
  }, [isOpen]);

  // Release the provider checkout when the modal closes.
  useEffect(() => {
    if (!isOpen) {
      teardownCheckout();
    }
  }, [isOpen, teardownCheckout]);

  // Release the provider checkout when the component unmounts.
  useEffect(() => {
    return () => {
      teardownCheckout();
    };
  }, [teardownCheckout]);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="sm:max-w-[400px] border-none shadow-none bg-transparent p-0"
        showCloseButton={false}
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Pasarela de Pago Izipay</DialogTitle>
        </DialogHeader>

        {fase === "preparando" && (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-[32px] shadow-2xl gap-4">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
              Iniciando pasarela...
            </p>
          </div>
        )}

        {fase === "recuperando" && (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-[32px] shadow-2xl gap-4">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
              Verificando el pago...
            </p>
          </div>
        )}

        {fase === "error" && errorPreparacion && (
          <div
            role="alert"
            className="flex flex-col items-center justify-center gap-4 p-8 bg-white rounded-[32px] shadow-2xl"
          >
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-center text-sm font-semibold text-gray-700">
              {errorPreparacion.message}
            </p>
            {errorPreparacion.code && (
              <p className="text-xs font-bold uppercase tracking-widest text-gray-400">
                Código: {errorPreparacion.code}
              </p>
            )}
            <Button variant="outline" onClick={onClose}>
              Cerrar
            </Button>
          </div>
        )}

        <div id="izipay-checkout" className="w-full" />
      </DialogContent>
    </Dialog>
  );
}
