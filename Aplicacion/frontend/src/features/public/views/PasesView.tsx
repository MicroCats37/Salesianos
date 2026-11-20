import { CreditCard, Ticket, UserRound } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";

const PASOS = [
  {
    titulo: "Elige tu pase",
    detalle: "El pase es nominativo: cada entrada pertenece a una persona.",
    Icono: Ticket,
  },
  {
    titulo: "Completa el pago",
    detalle: "El precio y la moneda los fija el servidor en el momento del pago.",
    Icono: CreditCard,
  },
  {
    titulo: "Asigna los beneficiarios",
    detalle:
      "Después del pago, el acceso permite elegir quién usa cada pase.",
    Icono: UserRound,
  },
] as const;

/**
 * PASS-01 - the purchase of the party passes.
 *
 * The pass is NOT a branch of the sports registration: it gives access to
 * the party and it says so. The three steps are the real ones of the flow
 * and they are stated before the catalogue, because the visitor arrives
 * here with the question "qué es esto" before "cuánto cuesta".
 */
export function PasesView() {
  return (
    <div className="flex flex-col gap-8">
      <RouteHero
        pageId="PASS-01"
        title="Comprar un pase de fiesta"
        description="El pase da acceso nominativo a la fiesta, sin inscripción deportiva. Elige el pase, confirma la cantidad y completa el pago: el precio lo fija el servidor."
        tone="band"
      />

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-section-title text-foreground">
            Cómo funciona la compra
          </h2>
        </div>
        <ol className="grid gap-3 sm:grid-cols-3">
          {PASOS.map((paso, indice) => {
            const Icono = paso.Icono;

            return (
              <li
                key={paso.titulo}
                className="flex flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-card p-4 transition-all duration-(--motion-duration-base) hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[var(--elevation-sm)]"
              >
                <span className="flex items-center gap-2">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Icono className="size-4" aria-hidden="true" />
                    <span className="sr-only">Paso {indice + 1}</span>
                  </span>
                  <span className="text-sm font-bold text-foreground">
                    {paso.titulo}
                  </span>
                </span>
                <p className="text-caption text-muted-foreground">
                  {paso.detalle}
                </p>
              </li>
            );
          })}
        </ol>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-section-title text-foreground">
            El catálogo de pases
          </h2>
        </div>
        <RouteEmptyState
          icon={Ticket}
          title="El catálogo de pases todavía no está disponible"
          description="Los pases y sus precios los publica el catálogo del backend, con un precio por preventa y otro por venta regular. Esta sección se completará con esa fuente; hasta entonces no se muestra ningún precio que el servidor no haya confirmado."
        />
      </section>
    </div>
  );
}
