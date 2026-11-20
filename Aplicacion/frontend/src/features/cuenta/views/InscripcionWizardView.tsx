import { ClipboardList, CreditCard, Package } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";

const PASOS = [
  {
    nombre: "Paquete",
    detalle: "La promoción y el paquete que secontrata.",
    Icono: Package,
  },
  {
    nombre: "Equipos y promoción",
    detalle: "Las disciplinas y los equipos que se anotan.",
    Icono: ClipboardList,
  },
  {
    nombre: "Declaraciones",
    detalle: "Las aceptaciones legales de la inscripción.",
    Icono: CreditCard,
  },
] as const;

/**
 * SPORT-01 - the wizard of a registration.
 *
 * The three steps are the ones the backend models: the package, the teams
 * and the legal acceptances. The wizard shows the STRUCTURE of the flow
 * with the state each step is in; it never sends a form that the service of
 * inscriptions cannot receive yet.
 */
export function InscripcionWizardView() {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SPORT-01"
        title="Crear una inscripción deportiva"
        description="Tres pasos: el paquete que se contrata, los equipos que se anotan y las declaraciones que el comité valida."
        tone="band"
      />

      <ol className="flex flex-col gap-3">
        {PASOS.map((paso, indice) => {
          const Icono = paso.Icono;

          return (
            <li
              key={paso.nombre}
              className="flex items-start gap-4 rounded-[var(--radius-lg)] border border-border bg-card p-4"
            >
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-bold text-muted-foreground">
                <Icono className="size-4" aria-hidden="true" />
                <span className="sr-only">Paso {indice + 1}</span>
              </span>
              <span className="flex min-w-0 flex-col gap-1">
                <span className="text-sm font-bold text-foreground">
                  {indice + 1}. {paso.nombre}
                </span>
                <span className="text-caption text-muted-foreground">
                  {paso.detalle}
                </span>
              </span>
            </li>
          );
        })}
      </ol>

      <RouteEmptyState
        icon={ClipboardList}
        title="El asistente se habilita con el catálogo"
        description="El primer paso elige el paquete vigente y el precio lo fija el servidor: el asistente se completará cuando el catálogo y el servicio de cotizaciones estén conectados. Nada de lo que se escriba aquí se cobra antes de que el comité valide la inscripción."
      />
    </div>
  );
}
