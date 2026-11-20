"use client";

import Link from "next/link";
import { ShellErrorState } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";

/**
 * The error boundary of the administration area.
 *
 * The message shown is the one the backend produced: this boundary only
 * offers the way forward.
 */
export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto flex w-full max-w-page flex-col gap-6 py-8">
      <ShellErrorState
        title="No pudimos cargar la información"
        description="El módulo no respondió. Vuelve a intentarlo; si el problema continúa, informa al soporte."
        accion={{ label: "Reintentar", onClick: reset }}
      />

      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">
          Referencia: {error.digest}
        </p>
      ) : null}

      <Button variant="outline" asChild className="min-h-11">
        <Link href={RUTAS.administracion.resumen}>Volver al resumen</Link>
      </Button>
    </div>
  );
}
