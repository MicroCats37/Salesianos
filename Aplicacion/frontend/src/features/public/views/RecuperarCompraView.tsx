import { KeyRound, LogIn } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";
import { RecuperarCompraForm } from "../components/RecuperarCompraForm";

/**
 * REC-01 - the recovery of the access to a purchase.
 *
 * The visitor lost the link. The recovery does NOT show the purchase: it
 * sends a new access. The page says so, and it offers the two ways back
 * into the product: the session and the store.
 *
 * The answer is NEUTRAL: it is the same whether the purchase exists or not,
 * so the page never becomes an oracle about somebody else's purchase.
 */
export function RecuperarCompraView() {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="REC-01"
        title="Recuperar el acceso a una compra"
        description="Si perdiste el enlace de tu compra, puedes pedir uno nuevo. La compra no se muestra aquí: se envía un acceso nuevo a quien la hizo."
        actions={
          <>
            <Button asChild className="min-h-11">
              <Link href={RUTAS.auth.login}>
                <LogIn className="size-4" aria-hidden="true" />
                Entrar a mi cuenta
              </Link>
            </Button>
            <Button variant="outline" asChild className="min-h-11">
              <Link href={RUTAS.publico.tienda}>Volver a la tienda</Link>
            </Button>
          </>
        }
      />

      <div className="mx-auto flex w-full max-w-[480px] flex-col gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-5 shadow-[var(--elevation-sm)] sm:p-6">
        <div className="flex flex-col gap-1">
          <h2 className="flex items-center gap-2 text-section-title text-foreground">
            <KeyRound className="size-4 text-primary" aria-hidden="true" />
            Solicitar un enlace nuevo
          </h2>
          <p className="text-caption text-muted-foreground">
            Escribe el correo de la compra y el número de orden. Con eso
            comprobamos si hay una compra que recuperar.
          </p>
        </div>

        <RecuperarCompraForm />
      </div>

      <RouteEmptyState
        icon={KeyRound}
        title="La recuperación no vuelve a abrir ninguna compra"
        description="Pedir un enlace nuevo no crea una compra ni la modifica: solo reenvía el acceso a quien ya lo tenía. Y la respuesta es la misma exista o no una compra con esos datos."
      />
    </div>
  );
}
