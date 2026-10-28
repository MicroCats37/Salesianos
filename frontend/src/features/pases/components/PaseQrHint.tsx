"use client";

import { QrCode } from "lucide-react";

/**
 * PaseQrHint — who delivers the QR of a pass.
 *
 * The QR is an ADMINISTRATIVE credential: the organization generates it and
 * delivers it at the accreditation. The buyer NEVER receives a QR credential
 * and the frontend never renders one
 * (`contract/api-wrapper-presenter-contract.md` §6: no credential travels in a
 * general read).
 */
export function PaseQrHint() {
  return (
    <p className="flex items-start gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
      <QrCode
        className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
        aria-hidden="true"
      />
      <span>
        El código QR de acceso lo genera y entrega la organización en la
        acreditación. El comprador nunca recibe una credencial QR: solo registra
        quién usará cada pase.
      </span>
    </p>
  );
}
