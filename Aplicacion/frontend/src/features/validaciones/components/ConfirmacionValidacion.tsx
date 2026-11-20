"use client";

import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChipVeredictoValidacion } from "./ChipVeredictoValidacion";
import { formatearInstante } from "../utils/validaciones.fecha.utils";
import type {
  ResultadoValidacion,
  VistaPreviaValidacion,
} from "../types/validacion.types";

/**
 * ConfirmacionValidacion - the explicit confirmation of a validation.
 *
 * The confirm is a SEPARATE state, not a continuation of the preview
 * (`GOV-02-RB-05b`): it only appears when a preview said that the operation
 * is admissible, and it names what it is going to do.
 *
 * When the confirmation comes back, the outcome is shown as a fact: the
 * operator, the point, the instant and the units consumed. A replay — the
 * same idempotency key arriving twice — is shown as a replay, never as a
 * second consumption.
 */
export function ConfirmacionValidacion({
  vistaPrevia,
  resultado,
  onConfirmar,
  ocupado = false,
  etiquetaAccion = "Confirmar la validación",
}: {
  /** The preview that precedes the confirmation. */
  vistaPrevia?: VistaPreviaValidacion;
  /** The outcome, when the confirmation already happened. */
  resultado?: ResultadoValidacion;
  /** The confirmation. It is OPTIONAL: without it the state says why. */
  onConfirmar?: () => void;
  /** Whether the confirmation is in flight. */
  ocupado?: boolean;
  /** The name of the action, in the words of the operation. */
  etiquetaAccion?: string;
}) {
  if (resultado) {
    const instante = formatearInstante(resultado.instante);
    return (
      <section
        aria-label="Resultado de la validación"
        className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-border bg-surface-recessed p-4"
      >
        <div className="flex flex-wrap items-center gap-2">
          <ShieldCheck
            className={resultado.validado ? "size-4 text-success" : "size-4 text-destructive"}
            aria-hidden="true"
          />
          <h3 className="text-sm font-semibold text-foreground">
            {resultado.validado
              ? "La validación quedó registrada"
              : "La validación no se registró"}
          </h3>
          <ChipVeredictoValidacion veredicto={resultado.veredicto} />
        </div>

        <p className="text-caption text-muted-foreground">
          {resultado.punto} · {resultado.operador}
          {instante ? ` · ${instante}` : ""}
        </p>
        <p className="text-caption text-muted-foreground tabular-nums">
          Unidades consumidas: {resultado.cantidad_consumida}
        </p>

        {resultado.repetida ? (
          <p
            role="status"
            className="rounded-[var(--radius-sm)] border border-warning/45 bg-warning/10 p-2 text-caption text-foreground"
          >
            Esta confirmación ya se había registrado antes: no se consumió una
            segunda vez.
          </p>
        ) : null}
      </section>
    );
  }

  if (!vistaPrevia) {
    return (
      <section
        aria-label="Confirmación de la validación"
        className="rounded-[var(--radius-md)] border border-dashed border-border p-4"
      >
        <p className="text-sm text-muted-foreground">
          Todavía no hay una vista previa: primero hay que comprobar la
          credencial. Comprobar no consume, y sin una comprobación no se
          ofrece la confirmación.
        </p>
      </section>
    );
  }

  if (!vistaPrevia.puede_validar) {
    return (
      <section
        aria-label="Confirmación de la validación"
        className="rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 p-4"
      >
        <p className="text-sm font-semibold text-foreground">
          No se puede validar
        </p>
        <p className="text-caption text-muted-foreground">
          {vistaPrevia.veredicto.estado.etiqueta}. No se ofrece la
          confirmación porque el servidor no la admite.
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Confirmación de la validación"
      className="flex flex-col gap-3 rounded-[var(--radius-md)] border border-border bg-surface-recessed p-4"
    >
      <p className="text-sm text-foreground">
        Confirmar registra la validación con tu nombre, con el punto de control
        y con el instante. No se puede deshacer.
      </p>
      <Button
        type="button"
        onClick={onConfirmar}
        disabled={!onConfirmar || ocupado}
        className="min-h-11 sm:w-fit"
      >
        {ocupado ? "Registrando…" : etiquetaAccion}
      </Button>
      {!onConfirmar ? (
        <p className="text-caption text-muted-foreground">
          El servicio de validación todavía no está conectado en el backend:
          la confirmación no sale de este dispositivo.
        </p>
      ) : null}
    </section>
  );
}
