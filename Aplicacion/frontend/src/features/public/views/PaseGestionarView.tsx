import { ShieldCheck, UserRound } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";

/**
 * PASS-02 - the assignment of the beneficiaries of a purchase.
 *
 * The route is reached with a token in the URL: the token IS the credential
 * and its expiry is the business of the server. The page never asks for a
 * session, because the visitor who bought the passes may not have one.
 */
export function PaseGestionarView({ token }: { token: string }) {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="PASS-02"
        title="Asignar los beneficiarios de tu compra"
        description="Indica quién usa cada pase. El acceso llega con un enlace propio y sólo permite trabajar sobre esa compra: no hay sesión ni datos de otras compras."
        facts={[{ label: "Acceso", value: `${token.slice(0, 8)}…` }]}
      />

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-section-title text-foreground">
            Cómo se asigna un beneficiario
          </h2>
        </div>
        <ol className="grid gap-3 sm:grid-cols-3">
          <li className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-card p-4 transition-all duration-(--motion-duration-base) hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[var(--elevation-sm)]">
            <span className="flex items-center gap-2">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <UserRound className="size-4" aria-hidden="true" />
              </span>
              <span className="text-sm font-bold text-foreground">
                Elige a la persona
              </span>
            </span>
            <p className="text-caption text-muted-foreground">
              Se busca por documento y el servidor comprueba que exista.
            </p>
          </li>

          <li className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-card p-4 transition-all duration-(--motion-duration-base) hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[var(--elevation-sm)]">
            <span className="flex items-center gap-2">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <ShieldCheck className="size-4" aria-hidden="true" />
              </span>
              <span className="text-sm font-bold text-foreground">
                Asigna el pase
              </span>
            </span>
            <p className="text-caption text-muted-foreground">
              Sólo se puede asignar sobre una compra pagada.
            </p>
          </li>

          <li className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-card p-4 transition-all duration-(--motion-duration-base) hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[var(--elevation-sm)]">
            <span className="flex items-center gap-2">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <ShieldCheck className="size-4" aria-hidden="true" />
              </span>
              <span className="text-sm font-bold text-foreground">
                Revisa y revoca
              </span>
            </span>
            <p className="text-caption text-muted-foreground">
              Un beneficiario asignado se puede revocar, y queda registrado.
            </p>
          </li>
        </ol>
      </section>

      <RouteEmptyState
        icon={UserRound}
        title="Los beneficiarios se mostrarán aquí"
        description="La compra, sus pases y sus beneficiarios llegan del servicio de pases con el token de acceso. Esta pantalla se completará con esa fuente; hasta entonces no se inventa ninguna asignación."
      />
    </div>
  );
}
