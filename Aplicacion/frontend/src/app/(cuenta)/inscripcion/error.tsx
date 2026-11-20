"use client";

import { ShellErrorState } from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";

/**
 * The error boundary of the wizard of a registration.
 *
 * The way back is the account hub: the visitor was creating a registration,
 * not reading a record.
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
        title="No pudimos abrir el asistente"
        description="No pudimos leer el catálogo de la edición en este momento. Vuelve a intentarlo en unos segundos: no se ha creado ninguna inscripción."
        accion={{ label: "Reintentar", onClick: reset }}
      />
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">
          Referencia: {error.digest}
        </p>
      ) : null}
      <Button variant="ghost" asChild>
        <a href={RUTAS.cuenta.miCuenta}>Volver a mi cuenta</a>
      </Button>
    </main>
  );
}
