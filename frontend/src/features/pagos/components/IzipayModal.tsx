"use client";

/**
 * IzipayModal — Izipay Web Core 2.0 popup for payment.
 *
 * Flow:
 * 1. Modal opens → calls backend GET /pagos/izipay/preparar/{inscripcionId}
 * 2. Backend returns session token + public config (no secrets)
 * 3. Waits for window.Izipay SDK to be ready (bounded polling)
 * 4. Builds SDK config and calls checkout.LoadForm()
 * 5. SDK opens popup; on callback (code === "00") → POST /pagos/izipay/confirmar
 * 6. On backend success → calls onSuccess() and closes
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import type { IzipayConfirmOut } from "../schemas/pago.schema";

declare global {
  interface Window {
    Izipay?: {
      LoadForm(options: {
        authorization: string;
        keyRSA?: string;
        callbackResponse: (response: IzipayResponse) => void;
      }): void;
    };
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

// ── SDK response type (partial — only fields we use) ──────────────────────────

interface IzipayResponse {
  code: string;
  message?: string;
  transactionId?: string;
  paymentMethod?: string;
  brand?: string;
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

function buildAddressData(rawData: Record<string, unknown>) {
  return {
    ...rawData,
    firstName: sanitizeNamePart(rawData?.firstName, "Juan"),
    lastName: sanitizeNamePart(rawData?.lastName, "Perez"),
    email: sanitizeEmail(rawData?.email),
    phoneNumber: sanitizePhone(rawData?.phoneNumber),
    street: "Av. Arequipa 123",
    city: "Lima",
    state: "Lima",
    country: "PE",
    postalCode: "00001",
    documentType: sanitizeText(rawData?.documentType) || "DNI",
    document: sanitizeDocument(rawData?.document),
  };
}

// ── Props ──────────────────────────────────────────────────────────────────────

export interface IzipayModalProps {
  /** Controls modal visibility */
  isOpen: boolean;
  /** Called when modal should close (user dismissed or flow ended) */
  onClose: () => void;
  /** The inscription to pay for */
  inscripcionId: string;
  /** Called on confirmed payment success — parent should refetch inscription state */
  onSuccess: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function IzipayModal({
  isOpen,
  onClose,
  inscripcionId,
  onSuccess,
}: IzipayModalProps) {
  const [loading, setLoading] = useState(false);
  const checkoutRef = useRef<{ Unmount?: () => void } | null>(null);

  const handleLaunchIzipay = useCallback(async () => {
    setLoading(true);
    try {
      // Step 1: Get session token from backend
      const prepareRes = await api.get<{
        success: boolean;
        data: Record<string, unknown>;
        error?: { message?: string };
      }>(`/pagos/izipay/preparar/${inscripcionId}`);
      const prepareData = prepareRes.data;

      if (!prepareData.success || !prepareData.data?.token) {
        const msg =
          (prepareData.error as { message?: string })?.message ||
          "No se pudo generar el token de pago.";
        toast.error(msg);
        onClose();
        return;
      }

      const d = prepareData.data;

      // Step 2: Wait for SDK global
      const sdkReady = await waitForIzipaySdk();
      if (!sdkReady || !window.Izipay) {
        toast.error("El SDK de Izipay no se ha cargado correctamente.");
        onClose();
        return;
      }

      // Step 3: Build SDK config — all values come from the backend prepare response
      const now = String(Date.now() * 1000);
      const amount = normalizeAmount(d.amount);
      const orderNumber = String(d.order_number ?? "");
      const transactionId = String(d.transaction_id ?? "");

      // authorization: check multiple fallbacks per Izipay Web Core 2.0 reference
      const authorization = String(
        (d as Record<string, unknown>).authorization ||
          (d as Record<string, unknown>).token ||
          d.token ||
          "",
      );

      const finalConfig = {
        action: "pay", // mandatory per Izipay Web Core 2.0 SDK contract
        merchantCode: String(d.merchant_code ?? ""),
        transactionId,
        order: {
          orderNumber,
          currency: String(d.currency ?? "PEN"),
          amount,
          processType: "AT",
          payMethod: "CARD,QR,YAPE_CODE,PAGO_PUSH",
          merchantBuyerId: String(d.buyer_email ?? "00000000"),
          dateTimeTransaction: now,
        },
        billing: buildAddressData({
          firstName: d.buyer_name ?? "Cliente",
          lastName: d.buyer_surname ?? "Venta",
          email: d.buyer_email ?? "pagos@salesianos.pe",
          phoneNumber: "999999999",
          documentType: "DNI",
          document: "00000000",
        }),
        shipping: buildAddressData({
          firstName: d.buyer_name ?? "Cliente",
          lastName: d.buyer_surname ?? "Venta",
          email: d.buyer_email ?? "pagos@salesianos.pe",
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
        originEntry: String((d as Record<string, unknown>).originEntry ?? "WEB"),
      };

      // Step 4: Initialize checkout
      let checkout: { Unmount?: () => void };
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        checkout = new (window.Izipay as any)({ config: finalConfig });
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

      // Step 5: Define payment callback
      const callbackResponsePayment = async (
        izipayResponse: IzipayResponse,
      ) => {
        const methodUsed =
          izipayResponse.paymentMethod || izipayResponse.brand || "Izipay";

        if (izipayResponse.code === "00") {
          try {
            const confirmRes = await api.post<{
              success: boolean;
              data: IzipayConfirmOut;
              error?: { message?: string };
            }>("/pagos/izipay/confirmar", { kr_answer: izipayResponse });
            if (confirmRes.data.success) {
              toast.success(`Pago con ${methodUsed} realizado con éxito.`);
              onSuccess();
              onClose();
            } else {
              const msg =
                (confirmRes.data.error as { message?: string })?.message ||
                "Error al confirmar el pago.";
              toast.error(msg);
              onClose();
            }
          } catch {
            toast.error(
              `Pago con ${methodUsed} detectado, pero falló la confirmación. Recarga la página.`,
              { duration: 8000 },
            );
            onClose();
          }
        } else {
          toast.error(
            izipayResponse.message || "El pago no fue aprobado por Izipay.",
          );
          onClose();
        }
      };

      // Step 6: Render the form (popup opens) — LoadForm is called on the checkout instance
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (checkout as any).LoadForm({
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
  }, [inscripcionId, onClose, onSuccess]);

  // Launch on open
  useEffect(() => {
    if (isOpen && inscripcionId) {
      void handleLaunchIzipay();
    }
  }, [isOpen, inscripcionId, handleLaunchIzipay]);

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
