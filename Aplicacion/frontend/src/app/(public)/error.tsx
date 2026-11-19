"use client";

import { ShellErrorState } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";

/**
 * The error boundary of this group.
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
        title="No pudimos cargar esta página"
        description={`El contenido no está disponible en este momento. Vuelve a intentarlo en unos segundos.`}
        accion={{ label: "Reintentar", onClick: reset }}
      />
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">
          Referencia: {error.digest}
        </p>
      ) : null}
      <Button variant="ghost" asChild>
        <a href="/">Ir al inicio</a>
      </Button>
    </main>
  );
}
