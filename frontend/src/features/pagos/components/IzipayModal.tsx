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
 * 7. On a verified payment → refresh the authoritative state (onSuccess) and
 *    close.
 */

import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getErrorMessage } from "@/errors";
import type { IzipayCallback } from "../schemas/pago.schema";
import {
  confirmarPagoIzipay,
  iniciarPagoIzipay,
} from "../services/pago.service";
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
  const [loading, setLoading] = useState(false);
  const checkoutRef = useRef<IzipayCheckout | null>(null);
  /**
   * One-shot guards. The checkout performs exactly two requests:
   * - `launchedRef` — one provider session per modal opening.
   * - `relayedRef` — one relay of the provider payload per session.
   */
  const launchedRef = useRef(false);
  const relayedRef = useRef(false);

  const handleLaunchIzipay = useCallback(async () => {
    if (launchedRef.current || !compraId) return;
    launchedRef.current = true;
    setLoading(true);
    try {
      // Step 1: Get session token from backend
      const prepareRes = await iniciarPagoIzipay(compraId);
      const prepareData = prepareRes.data;

      if (!prepareRes.success || !prepareData?.token) {
        const msg =
          prepareRes.error?.message || "No se pudo generar el token de pago.";
        toast.error(msg);
        onClose();
        return;
      }

      const d = prepareData;

      // Step 2: Wait for SDK global
      const sdkReady = await waitForIzipaySdk();
      if (!sdkReady || !window.Izipay) {
        toast.error("El SDK de Izipay no se ha cargado correctamente.");
        onClose();
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
        toast.error(msg);
        onClose();
        return;
      }

      // Step 5: Relay the provider payload — exactly once.
      const callbackResponsePayment = async (
        providerPayload: IzipayCallback,
      ) => {
        if (relayedRef.current) return;
        relayedRef.current = true;

        const methodUsed =
          providerPayload.response?.payMethod ??
          textoOpcional(providerPayload.paymentMethod) ??
          "Izipay";

        if (providerPayload.code !== "00") {
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
            toast.error(
              confirmRes.error?.message ||
                confirm?.response_message ||
                "Error al confirmar el pago.",
            );
            onClose();
            return;
          }

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
        } catch (err: unknown) {
          toast.error(
            `Pago con ${methodUsed} detectado, pero falló la confirmación. ${getErrorMessage(err)}`,
            { duration: 8000 },
          );
          onClose();
        }
      };

      // Step 6: Render the form (popup opens) — LoadForm is called on the checkout instance
      try {
        checkout.LoadForm({
          authorization,
          keyRSA: "RSA",
          callbackResponse: callbackResponsePayment,
        });
      } catch (sdkLoadError: unknown) {
        const msg =
          sdkLoadError instanceof Error
            ? sdkLoadError.message
            : "Error al abrir el formulario de pago.";
        toast.error(msg);
        onClose();
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Error al iniciar el pago con Izipay.";
      toast.error(msg);
      onClose();
    } finally {
      setLoading(false);
    }
  }, [compraId, onClose, onSuccess]);

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
    }
  }, [isOpen]);

  // Cleanup on unmount/close
  useEffect(() => {
    return () => {
      try {
        checkoutRef.current?.Unmount?.();
      } catch {
        // Ignore cleanup errors
      }
      checkoutRef.current = null;
    };
  }, []);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="sm:max-w-[400px] border-none shadow-none bg-transparent p-0"
        showCloseButton={false}
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Pasarela de Pago Izipay</DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex flex-col items-center justify-center p-12 bg-white rounded-[32px] shadow-2xl gap-4">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">
              Iniciando pasarela...
            </p>
          </div>
        )}

        <div id="izipay-checkout" className="w-full" />
      </DialogContent>
    </Dialog>
  );
}
