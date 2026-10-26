"use client";

import { RefreshCw, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

interface InscripcionErrorStateProps {
  message: string;
  onRetry: () => void;
  retrying?: boolean;
}

/**
 * Failure state of the inscription detail.
 *
 * It always offers the retry action: the detail is a client-side view over a
 * cached query, so a failed request is recoverable without leaving the page.
 */
export function InscripcionErrorState({
  message,
  onRetry,
  retrying = false,
}: InscripcionErrorStateProps) {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-16 sm:px-6">
      <div className="relative overflow-hidden rounded-3xl border border-rose-200 bg-rose-50/80 p-8 text-center shadow-sm">
        <div className="pointer-events-none absolute -right-12 -top-12 size-40 rounded-full bg-rose-200/40 blur-3xl" />
        <div className="relative mx-auto max-w-md space-y-4">
          <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-400 to-rose-600 text-white shadow-lg">
            <TriangleAlert className="size-6" />
          </span>
          <div className="space-y-1.5">
            <h2 className="text-xl font-black tracking-tight text-rose-900">
              No pudimos cargar la inscripcion
            </h2>
            <p className="text-sm leading-relaxed text-rose-700">{message}</p>
          </div>
          <Button
            type="button"
            onClick={onRetry}
            disabled={retrying}
            className="btn-brand-gradient btn-shine h-12 w-full rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg sm:w-auto"
          >
            <RefreshCw
              className={retrying ? "size-4 animate-spin" : "size-4"}
              aria-hidden="true"
            />
            {retrying ? "Reintentando..." : "Reintentar"}
          </Button>
        </div>
      </div>
    </div>
  );
}
