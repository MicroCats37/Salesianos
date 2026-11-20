"use client";

import { LogIn, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { ShellErrorState } from "@/components/shell/ShellState";
import {
  Alert,
  AlertAction,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSesionActual } from "@/features/auth/hooks/useSesionActual";
import { RUTAS } from "@/lib/routes";

/**
 * `PanelSesion` — the guard of the session of the account area.
 *
 * ACCOUNT-01 declares the state `S-06`: "session expired → sign in, preserving
 * the intent" (`GOV-02` RB-01).
 *
 * The cookie of the session is NOT the authority: it can outlive the access
 * token. The authority is `GET /auth/me` (`AuthController`, registered in
 * `Aplicacion/backend/config/api.py`), so the read decides whether the session
 * is still alive.
 *
 * The component says NOTHING when the session is fine: the account area draws
 * its own content and a guard that reports success is noise. It speaks only
 * when there is something to recover from:
 *
 * - `401` → the session expired: the way back is signing in again.
 * - any other failure → the recoverable error, with the message of the
 *   backend, verbatim.
 */
export function PanelSesion({ activo }: { activo: boolean }) {
  const { isPending, isError, error } = useSesionActual({ enabled: activo });

  if (!activo || (!isPending && !isError)) {
    return null;
  }

  if (isPending) {
    return (
      <div
        className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
        aria-busy="true"
      >
        <Skeleton className="h-4 w-64" />
      </div>
    );
  }

  const status = (error as { status?: number } | null)?.status;

  if (status === 401) {
    return (
      <Alert className="border-warning/45 bg-warning/12">
        <TriangleAlert className="size-4 text-warning" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          Tu sesión ya no está activa
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          Vuelve a entrar para seguir viendo tus inscripciones y tus compras.
          No hemos perdido nada: solo hay que volver a identificarte.
        </AlertDescription>
        <AlertAction className="mt-3">
          <Button variant="outline" size="sm" asChild>
            <Link href={RUTAS.auth.login}>
              <LogIn className="size-4" aria-hidden="true" />
              Entrar de nuevo
            </Link>
          </Button>
        </AlertAction>
      </Alert>
    );
  }

  return (
    <ShellErrorState
      title="No pudimos confirmar tu sesión"
      description={
        (error as { message?: string } | null)?.message ??
        "Vuelve a intentarlo en unos segundos."
      }
      className="border-border bg-surface-raised"
    />
  );
}
