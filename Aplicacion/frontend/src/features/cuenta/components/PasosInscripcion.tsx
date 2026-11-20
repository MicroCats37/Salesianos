import { CreditCard, GraduationCap, ShieldCheck, Users } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * The four steps of a registration.
 *
 * They come from the flow the committee validates: create, validate, pay,
 * enrol the people. The diagram tells the responsible WHERE their
 * registration is, so it is a journey and not a list of features.
 */
const PASOS = [
  {
    titulo: "Crear la inscripción",
    detalle: "Paquete, promoción y equipos de la promoción.",
    Icono: GraduationCap,
  },
  {
    titulo: "Validación del comité",
    detalle: "El comité revisará la nómina y las aceptaciones.",
    Icono: ShieldCheck,
  },
  {
    titulo: "Completar el pago",
    detalle: "La inscripción se activa cuando el pago queda confirmado.",
    Icono: CreditCard,
  },
  {
    titulo: "Inscribir personas",
    detalle: "Se asigna cada persona a su equipo y se reserva su cupo.",
    Icono: Users,
  },
] as const;

export interface PasosInscripcionProps {
  /**
   * The step the registration is on, from 1 to 4.
   *
   * `null` means "we do not know yet": every step is drawn as pending
   * instead of pretending that the first one is done.
   */
  pasoActual?: number | null;
  className?: string;
}

/**
 * PasosInscripcion - the journey of a registration.
 *
 * The diagram is an ORDERED LIST: it says what happens before what. The
 * current step is marked with the gold rule and with `aria-current="step"`,
 * so the journey is read with the eyes and with the screen reader.
 */
export function PasosInscripcion({
  pasoActual = null,
  className,
}: PasosInscripcionProps) {
  return (
    <ol className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", className)}>
      {PASOS.map((paso, indice) => {
        const numero = indice + 1;
        const completado = pasoActual !== null && numero < pasoActual;
        const actual = pasoActual === numero;
        const Icono = paso.Icono;

        return (
          <li
            key={paso.titulo}
            aria-current={actual ? "step" : undefined}
            className={cn(
              "relative flex flex-col gap-2 rounded-[var(--radius-xl)] border bg-background p-4 shadow-[var(--elevation-sm)] transition-colors duration-(--motion-duration-fast)",
              actual
                ? "border-accent bg-card shadow-[var(--elevation-md)]"
                : "border-border bg-card hover:border-border-strong",
            )}
          >
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                  actual
                    ? "bg-accent text-accent-foreground"
                    : "bg-muted text-muted-foreground",
                )}
              >
                {completado ? (
                  <Icono className="size-4" aria-hidden="true" />
                ) : (
                  numero
                )}
              </span>
              <span className="text-sm font-semibold text-foreground">
                {paso.titulo}
              </span>
            </span>
            <p className="text-caption text-muted-foreground">{paso.detalle}</p>
          </li>
        );
      })}
    </ol>
  );
}
