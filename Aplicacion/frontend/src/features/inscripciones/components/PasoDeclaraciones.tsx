"use client";

import type { LucideIcon } from "lucide-react";
import { FileText, Heart, ImageIcon } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";

export interface Declaraciones {
  bases: boolean;
  aptitudFisica: boolean;
  imagen: boolean;
}

export const DECLARACIONES_INICIALES: Declaraciones = {
  bases: false,
  aptitudFisica: false,
  imagen: false,
};

const DECLARACIONES: Array<{
  clave: keyof Declaraciones;
  titulo: string;
  detalle: string;
  Icono: LucideIcon;
}> = [
  {
    clave: "bases",
    titulo: "Acepto las bases del evento",
    detalle:
      "He leído y acepto las bases oficiales del evento Salesianos FEST 2026.",
    Icono: FileText,
  },
  {
    clave: "aptitudFisica",
    titulo: "Declaro estar apta/o físicamente",
    detalle:
      "Declaro que me encuentro en condiciones físicas adecuadas para participar en las disciplinas seleccionadas.",
    Icono: Heart,
  },
  {
    clave: "imagen",
    titulo: "Autorizo el uso de mi imagen",
    detalle:
      "Autorizo a los organizadores a utilizar fotografías y vídeos de mi participación para fines promocionales.",
    Icono: ImageIcon,
  },
];

export interface PasoDeclaracionesProps {
  /** The declarations: they live in the LOCAL state of the wizard. */
  declaraciones: Declaraciones;
  onCambiar: (clave: keyof Declaraciones, valor: boolean) => void;
  /** Whether the three declarations are accepted. */
  completas: boolean;
}

/**
 * PasoDeclaraciones - the declarations of the last step.
 *
 * It is COPIED from the previous frontend
 * (`frontend/src/features/inscripciones/components/steps/StepDeclarations.tsx`)
 * and adapted: the fake checkbox of the legacy is the `Checkbox` of the
 * project, so the keyboard, the focus and the announcement are the real ones.
 *
 * The declarations are NOT fields of the registration: the backend records
 * the acceptances per person. They live in the local state of the wizard and
 * they are a CONDITION to send, checked BEFORE the payload leaves the
 * browser.
 */
export function PasoDeclaraciones({
  declaraciones,
  onCambiar,
  completas,
}: PasoDeclaracionesProps) {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3">
        {DECLARACIONES.map((declaracion) => {
          const marcada = declaraciones[declaracion.clave];
          const id = `declaracion-${declaracion.clave}`;

          return (
            <label
              key={declaracion.clave}
              htmlFor={id}
              className="flex cursor-pointer items-start gap-3 rounded-[var(--radius-lg)] border border-border bg-card p-4 transition-colors duration-(--motion-duration-fast) hover:border-border-strong focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/30"
            >
              <Checkbox
                id={id}
                checked={marcada}
                onCheckedChange={(valor) =>
                  onCambiar(declaracion.clave, valor === true)
                }
                className="mt-1 size-5"
              />

              <span
                aria-hidden="true"
                className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-accent/20 text-accent"
              >
                <declaracion.Icono className="size-5" />
              </span>

              <span className="flex min-w-0 flex-1 flex-col gap-1">
                {/*
                 * The title of the declaration is a SPAN and not a `Label`:
                 * the card is already a `<label>`, and a label inside a label
                 * is invalid HTML. The card keeps the association with the
                 * checkbox through its own `htmlFor`.
                 */}
                <span className="cursor-pointer text-sm font-semibold text-foreground">
                  {declaracion.titulo}
                </span>
                <span className="text-caption leading-relaxed text-muted-foreground">
                  {declaracion.detalle}
                </span>
              </span>
            </label>
          );
        })}
      </div>

      {!completas ? (
        <p className="text-caption text-muted-foreground">
          Faltan{" "}
          {
            DECLARACIONES.filter(
              (declaracion) => !declaraciones[declaracion.clave],
            ).length
          }{" "}
          declaraciones por aceptar. La inscripción no se envía hasta que las
          tres estén marcadas.
        </p>
      ) : (
        <p className="text-caption font-semibold text-success">
          Las tres declaraciones están aceptadas: la inscripción puede
          registrarse.
        </p>
      )}
    </div>
  );
}
