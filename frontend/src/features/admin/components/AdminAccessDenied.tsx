"use client";

import { ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";

export interface AdminAccessDeniedProps {
  /** The public message returned by the backend, when there is one. */
  message?: string;
}

/**
 * "Acceso denegado" screen of the administration area.
 *
 * The backend is the authority: this screen appears when it refused the
 * request (403) or when it confirmed that the caller is not an
 * administrator. A 403 means the caller is authenticated but not authorized;
 * the session stays active so the user can return to the dashboard.
 */
export function AdminAccessDenied({ message }: AdminAccessDeniedProps) {
  const router = useRouter();
  const [isLeaving, setIsLeaving] = useState(false);

  function handleLeave() {
    setIsLeaving(true);
    router.replace("/dashboard");
  }

  return (
    <div className="surface-page-gradient flex min-h-svh w-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg rounded-3xl border border-rose-200 bg-white p-8 text-center shadow-sm ring-1 ring-rose-100">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
          <ShieldAlert className="size-7" />
        </div>

        <h1 className="mt-5 text-2xl font-black tracking-tight text-slate-900">
          Acceso denegado
        </h1>

        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          {message ??
            "Esta sección es exclusiva del comité organizador. Tu sesión se mantiene activa y puedes volver al panel."}
        </p>

        <Button
          type="button"
          variant="ghost"
          onClick={handleLeave}
          disabled={isLeaving}
          className="btn-brand-gradient btn-shine mt-6 h-11 w-full rounded-full text-xs font-black uppercase tracking-widest"
        >
          {isLeaving ? "Volviendo..." : "Volver al panel"}
        </Button>
      </div>
    </div>
  );
}
