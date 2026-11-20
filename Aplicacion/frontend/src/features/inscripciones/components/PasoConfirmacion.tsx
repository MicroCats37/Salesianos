"use client";

import { ShieldCheck } from "lucide-react";
import type { PaqueteCatalogo } from "../types/inscripcion.types";

export interface PasoConfirmacionProps {
  /** The chosen package, exactly as the catalogue publishes it. */
  paquete: PaqueteCatalogo | null;
}

/**
 * PasoConfirmacion - the last step of the wizard.
 *
 * It names the EFFECT of the action, because the action creates a
 * registration and opens a pending purchase (S-10, SH-03 section 1).
 *
 * The wording is the one of the domain: an unpaid purchase NEVER grants a
 * cup (RN-I02, QA-I01), so the confirmation says that the cupos are enabled
 * when the payment is confirmed and not before.
 *
 * It does not ask for a card: the payment happens in the checkout of the
 * commerce module, which this packet does not own.
 */
export function PasoConfirmacion(props: PasoConfirmacionProps) {
  const paquete = props.paquete;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <ShieldCheck className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-section-title text-foreground">
          Qué pasa al confirmar
        </h3>
      </div>

      <ol className="flex flex-col gap-3">
        <li className="flex gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3">
          <span
            aria-hidden="true"
            className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground"
          >
            1
          </span>
          <span className="text-sm leading-relaxed text-foreground">
            Se registra tu inscripción
            {paquete ? " para el paquete " + paquete.nombre : ""} con los
            equipos que declaraste.
          </span>
        </li>

        <li className="flex gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3">
          <span
            aria-hidden="true"
            className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground"
          >
            2
          </span>
          <span className="text-sm leading-relaxed text-foreground">
            Se abre una compra pendiente con el precio del catálogo. Todavía
            no se cobra nada.
          </span>
        </li>

        <li className="flex gap-3 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3">
          <span
            aria-hidden="true"
            className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground"
          >
            3
          </span>
          <span className="text-sm leading-relaxed text-foreground">
            Cuando el pago se confirme, los cupos se habilitan y ya puedes
            asignar las personas a los equipos.
          </span>
        </li>
      </ol>

      <p className="text-caption text-muted-foreground">
        Si ya existía una inscripción para este paquete, el servidor devuelve
        esa misma inscripción y su compra pendiente: no se crea una segunda
        ni se cobra dos veces.
      </p>
    </div>
  );
}
