"use client";

import { ShellErrorState } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";

/**
 * The error boundary of the detail of a purchase.
 *
 * The way back is the list of the purchases, not the home page: the reader
 * was reading a purchase, not the whole product.
 */
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[60svh] w-full max-w-[720px] flex-col justify-center gap-6 px-4 py-12 sm:px-6">
      <ShellErrorState
        title="No pudimos cargar esta compra"
        description="No pudimos leer el detalle en este momento. Vuelve a intentarlo en unos segundos."
        accion={{ label: "Reintentar", onClick: reset }}
      />
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">
          Referencia: {error.digest}
        </p>
      ) : null}
      <Button variant="ghost" asChild>
        <a href={RUTAS.cuenta.misCompras}>Volver a mis compras</a>
      </Button>
    </main>
  );
}
