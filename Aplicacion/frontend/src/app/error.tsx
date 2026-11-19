"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

/**
 * The global error boundary.
 *
 * It is a Client Component because it needs `reset()`. The message shown is
 * the one the backend produced; this boundary only offers the way forward.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // The error is reported, never silenced.
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-svh max-w-[640px] flex-col justify-center gap-6 px-4 py-16 sm:px-6">
      <p className="text-eyebrow-brand text-primary">Error</p>
      <div className="flex flex-col gap-3">
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          Algo se rompió por el camino
        </h1>
        <p className="text-muted-foreground">
          {error.message ||
            "No pudimos completar esta operación. Vuelve a intentarlo o regresa al inicio."}
        </p>
        {error.digest ? (
          <p className="font-mono text-xs text-muted-foreground">
            Referencia: {error.digest}
          </p>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-3">
        <Button onClick={reset}>Reintentar</Button>
        <Button variant="outline" asChild>
          <a href="/">Ir al inicio</a>
        </Button>
      </div>
    </main>
  );
}
