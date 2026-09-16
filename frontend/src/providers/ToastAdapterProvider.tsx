"use client";

import { type ReactNode, useEffect } from "react";
import { toast } from "sonner";
import { configureToast } from "@/errors/toast-adapter";

/**
 * Configura el adaptador de toasts (swappable) con sonner.
 * Sin esto, notify.error() solo hace console.error — los errores no se ven.
 */
export function ToastAdapterProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    configureToast(toast.error, toast.success);
  }, []);

  return <>{children}</>;
}
