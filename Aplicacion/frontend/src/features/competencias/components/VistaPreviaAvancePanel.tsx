import { Eye } from "lucide-react";
import { ChipBloqueo } from "./ChipEstadoCompetencia";
import type { VistaPreviaAvance } from "../types/competencia.types";

/**
 * VistaPreviaAvancePanel - what the advance WOULD do.
 *
 * The preview NEVER writes (`GOV-02-RB-05b`, `QA-K04`): the preview and the
 * confirm are two different actions of the backend and the panel says so in
 * its own title, not only in the documentation.
 *
 * When the destination already happened, the panel shows the reason the
 * backend published and the confirm is not offered: the client never decides
 * that an advance is possible.
 */
export function VistaPreviaAvancePanel({
  vistaPrevia,
}: {
  vistaPrevia: VistaPreviaAvance;
}) {
  return (
    <section
      aria-labelledby="vista-previa-avance"
      className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3
          id="vista-previa-avance"
          className="flex items-center gap-2 text-sm font-semibold text-foreground"
        >
          <Eye className="size-4 text-info" aria-hidden="true" />
          Vista previa del avance
        </h3>
        <span className="rounded-full border border-border bg-surface-raised px-2 py-0.5 text-caption text-muted-foreground">
          Esta vista previa no escribe nada
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
        <div>
          <dt className="text-caption text-muted-foreground">Equipo que avanzaría</dt>
          <dd className="text-sm font-semibold text-foreground">
            {vistaPrevia.ganador_equipo_nombre}
          </dd>
        </div>
        <div>
          <dt className="text-caption text-muted-foreground">Slot de destino</dt>
          <dd className="text-sm text-foreground">{vistaPrevia.slot_destino}</dd>
        </div>
        <div>
          <dt className="text-caption text-muted-foreground">
            Ocupante actual del destino
          </dt>
          <dd className="text-sm text-foreground">
            {vistaPrevia.ocupante_actual_equipo_id ?? "El destino está libre"}
          </dd>
        </div>
        <div>
          <dt className="text-caption text-muted-foreground">Estado del avance</dt>
          <dd className="text-sm text-foreground">
            {vistaPrevia.ya_propagado
              ? "Ya estaba propagado"
              : vistaPrevia.puede_confirmar
                ? "El servidor admite confirmarlo ahora"
                : "El servidor no admite confirmarlo ahora"}
          </dd>
        </div>
      </dl>

      {vistaPrevia.bloqueado ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <ChipBloqueo
            motivo={vistaPrevia.motivo_bloqueo ?? "El destino ya transcurrió"}
          />
        </div>
      ) : null}
    </section>
  );
}
