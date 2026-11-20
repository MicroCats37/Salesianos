import { TriangleAlert } from "lucide-react";
import { ChipBloqueo } from "./ChipEstadoCompetencia";
import type { VistaPreviaCorreccion } from "../types/competencia.types";

/**
 * VistaPreviaCorreccionPanel - what a correction WOULD change.
 *
 * The preview NEVER writes (`GOV-02-RB-05b`): it names the descendants that
 * really change, one by one, so the operator sees the blast radius before
 * deciding (`RB-05` ADM-12, `QA-K05`).
 *
 * When a descendant already happened, the correction needs an EXPLICIT
 * authorisation and a REASON (`S-10`). The panel says so; it never offers the
 * confirmation on its own.
 */
export function VistaPreviaCorreccionPanel({
  vistaPrevia,
}: {
  vistaPrevia: VistaPreviaCorreccion;
}) {
  return (
    <section
      aria-labelledby="vista-previa-correccion"
      className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3
          id="vista-previa-correccion"
          className="flex items-center gap-2 text-sm font-semibold text-foreground"
        >
          <TriangleAlert className="size-4 text-warning" aria-hidden="true" />
          Vista previa de la corrección
        </h3>
        <span className="rounded-full border border-border bg-surface-raised px-2 py-0.5 text-caption text-muted-foreground">
          Esta vista previa no escribe nada
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
        <div>
          <dt className="text-caption text-muted-foreground">Ganador propuesto</dt>
          <dd className="text-sm font-semibold text-foreground">
            {vistaPrevia.ganador_nuevo_equipo_nombre}
          </dd>
        </div>
        <div>
          <dt className="text-caption text-muted-foreground">
            Descendientes que cambian
          </dt>
          <dd className="text-sm font-semibold text-foreground tabular-nums">
            {vistaPrevia.total_afectados}
          </dd>
        </div>
      </dl>

      {vistaPrevia.requiere_override ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <ChipBloqueo
            motivo="Un descendiente ya transcurrió: la corrección necesita autorización explícita y un motivo"
          />
        </div>
      ) : null}

      {vistaPrevia.descendientes.length > 0 ? (
        <ul className="mt-3 flex flex-col gap-2">
          {vistaPrevia.descendientes.map((descendiente) => (
            <li
              key={`${descendiente.encuentro_id}-${descendiente.slot}`}
              className="rounded-[var(--radius-sm)] border border-border bg-surface-raised p-2"
            >
              <p className="text-sm font-medium text-foreground">
                {descendiente.encuentro_id} · {descendiente.slot}
              </p>
              <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-caption text-muted-foreground">
                <li>
                  Cambia de verdad: {descendiente.afecta ? "sí" : "no"}
                </li>
                <li>
                  Sustituye el valor propagado:{" "}
                  {descendiente.reemplaza ? "sí" : "no"}
                </li>
                <li>
                  Vacía el slot: {descendiente.limpia_slot ? "sí" : "no"}
                </li>
                <li>
                  Anula el resultado derivado:{" "}
                  {descendiente.limpia_resultado ? "sí" : "no"}
                </li>
              </ul>
              {descendiente.bloqueado ? (
                <p className="mt-1 text-caption font-semibold text-destructive">
                  {descendiente.motivo_bloqueo ??
                    "Este descendiente ya transcurrió y no se puede tocar."}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
