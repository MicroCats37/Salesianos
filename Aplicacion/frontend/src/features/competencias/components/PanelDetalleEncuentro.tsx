"use client";

import { useId } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type {
  Encuentro,
  VistaPreviaAvance,
  VistaPreviaCorreccion,
} from "../types/competencia.types";
import {
  estadoEncuentro,
  etiquetaAccion,
} from "../utils/competencias.estados.utils";
import { formatearInstante } from "../utils/competencias.fecha.utils";
import { ChipBloqueo, ChipEstadoCompetencia } from "./ChipEstadoCompetencia";
import { VistaPreviaAvancePanel } from "./VistaPreviaAvancePanel";
import { VistaPreviaCorreccionPanel } from "./VistaPreviaCorreccionPanel";

/**
 * PanelDetalleEncuentro - the ONE match detail of the area.
 *
 * `GOV-02-RB-05a`: the detail of a match is reachable from the list, from the
 * agenda and from the bracket, and it is the SAME panel in the three places.
 * Two editors would be a defect, so this component owns the presentation of
 * an encounter and nothing else.
 *
 * The panel is a `Sheet` (`dialog` semantics): it traps the focus, it
 * restores it to the trigger on close and it fits a small viewport as a
 * bottom drawer (90 vh) that becomes a side sheet from 768 up. The primitive
 * ships an English "Close" label, so its own close button is disabled and the
 * panel carries a Spanish one.
 *
 * It NEVER writes. The previews it shows say so, and the confirm is a
 * different action of the backend (`GOV-02-RB-05b`).
 */

export interface PanelDetalleEncuentroProps {
  /** The encounter, in its canonical shape. */
  encuentro: Encuentro;
  /** The preview of the advance, when the backend published it. */
  vistaPreviaAvance?: VistaPreviaAvance;
  /** The preview of the correction, when the backend published it. */
  vistaPreviaCorreccion?: VistaPreviaCorreccion;
  /**
   * The conflict declared by the backend.
   *
   * A version conflict NEVER auto-applies: it informs, it offers a reload and
   * it leaves the decision to the operator (`RB-05` ADM-11).
   */
  conflicto?: { mensaje: string };
  /** Whether the panel is open. */
  open: boolean;
  /** The state of the panel. */
  onOpenChange: (open: boolean) => void;
}

/** The name of a participant, or the honest absence of one. */
function nombreParticipante(encuentro: Encuentro, indice: number): string {
  return (
    encuentro.participantes.find((p) => p.slot === `PARTICIPANTE_${indice + 1}`)
      ?.equipo_nombre ?? "Sin equipo"
  );
}

/** The seed of a participant, or `null` when the backend did not publish one. */
function ordenParticipante(
  encuentro: Encuentro,
  indice: number,
): number | null {
  return (
    encuentro.participantes.find((p) => p.slot === `PARTICIPANTE_${indice + 1}`)
      ?.orden ?? null
  );
}

export function PanelDetalleEncuentro({
  encuentro,
  vistaPreviaAvance,
  vistaPreviaCorreccion,
  conflicto,
  open,
  onOpenChange,
}: PanelDetalleEncuentroProps) {
  const tituloId = useId();
  const descripcionId = useId();

  const equipo1 = nombreParticipante(encuentro, 0);
  const equipo2 = nombreParticipante(encuentro, 1);
  const semilla1 = ordenParticipante(encuentro, 0);
  const semilla2 = ordenParticipante(encuentro, 1);

  const hayMarcador =
    encuentro.puntaje_1 !== null || encuentro.puntaje_2 !== null;
  const inicio = formatearInstante(encuentro.inicio_programado);
  const fin = formatearInstante(encuentro.fin_programado);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        showCloseButton={false}
        className="data-[side=right]:inset-x-0 data-[side=right]:top-auto data-[side=right]:bottom-0 data-[side=right]:h-[90vh] data-[side=right]:w-full data-[side=right]:max-w-none data-[side=right]:rounded-t-[var(--radius-xl)] data-[side=right]:rounded-b-none data-[side=right]:border-t data-[side=right]:border-l-0 sm:data-[side=right]:inset-y-0 sm:data-[side=right]:top-0 sm:data-[side=right]:h-full sm:data-[side=right]:w-3/4 sm:data-[side=right]:max-w-sm sm:data-[side=right]:rounded-t-none sm:data-[side=right]:rounded-l-[var(--radius-xl)] sm:data-[side=right]:border-t-0 sm:data-[side=right]:border-l"
      >
        <SheetHeader>
          <SheetTitle id={tituloId} className="text-base">
            {equipo1} contra {equipo2}
          </SheetTitle>
          <SheetDescription id={descripcionId}>
            {encuentro.ronda_etiqueta} · encuentro {encuentro.orden}
          </SheetDescription>
        </SheetHeader>

        <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-4 pb-4">
          {conflicto ? (
            <div
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 p-3"
            >
              <p className="text-sm font-semibold text-foreground">
                Los datos cambiaron
              </p>
              <p className="text-caption text-muted-foreground">
                {conflicto.mensaje} Actualiza y revisa antes de guardar: nada se
                ha escrito.
              </p>
            </div>
          ) : null}

          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
              <dt className="text-caption text-muted-foreground">
                Participante 1
              </dt>
              <dd className="text-sm font-semibold text-foreground">
                {equipo1}
              </dd>
              <dd className="text-caption text-muted-foreground">
                {semilla1 === null
                  ? "Sin orden publicado"
                  : `Orden ${semilla1}`}
              </dd>
            </div>
            <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
              <dt className="text-caption text-muted-foreground">
                Participante 2
              </dt>
              <dd className="text-sm font-semibold text-foreground">
                {equipo2}
              </dd>
              <dd className="text-caption text-muted-foreground">
                {semilla2 === null
                  ? "Sin orden publicado"
                  : `Orden ${semilla2}`}
              </dd>
            </div>
            <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
              <dt className="text-caption text-muted-foreground">Marcador</dt>
              <dd className="text-sm font-semibold text-foreground tabular-nums">
                {hayMarcador
                  ? `${encuentro.puntaje_1 ?? "—"} — ${encuentro.puntaje_2 ?? "—"}`
                  : "Todavía no hay marcador"}
              </dd>
              {encuentro.marcador_detalle ? (
                <dd className="text-caption text-muted-foreground">
                  {encuentro.marcador_detalle}
                </dd>
              ) : null}
            </div>
            <div className="rounded-[var(--radius-md)] border border-border bg-surface-recessed p-3">
              <dt className="text-caption text-muted-foreground">Ganador</dt>
              <dd className="text-sm font-semibold text-foreground">
                {encuentro.ganador_equipo_nombre ?? "Sin ganador registrado"}
              </dd>
              <dd className="text-caption text-muted-foreground">
                {encuentro.siguiente_encuentro_id
                  ? `Avanza a ${encuentro.slot_destino ?? "un slot del cuadro"}`
                  : "No tiene destino en el cuadro"}
              </dd>
            </div>
          </dl>

          <div className="flex flex-col gap-2">
            <p className="text-caption text-muted-foreground">Estado</p>
            <div className="flex flex-wrap items-center gap-2">
              <ChipEstadoCompetencia
                estado={estadoEncuentro(encuentro.estado)}
              />
              {encuentro.es_bye ? <ChipBloqueo motivo="Pase libre" /> : null}
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <p className="text-caption text-muted-foreground">Programación</p>
            {inicio ? (
              <p className="text-sm text-foreground">
                <time dateTime={encuentro.inicio_programado ?? undefined}>
                  {inicio}
                </time>
                {fin ? (
                  <>
                    {" → "}
                    <time dateTime={encuentro.fin_programado ?? undefined}>
                      {fin}
                    </time>
                  </>
                ) : null}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Este encuentro todavía no tiene horario.
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1">
            <p className="text-caption text-muted-foreground">
              Acciones que admite el servidor en este estado
            </p>
            {encuentro.acciones.length > 0 ? (
              <ul className="flex flex-wrap gap-2">
                {encuentro.acciones.map((accion) => (
                  <li
                    key={accion}
                    className="rounded-full border border-border bg-surface-recessed px-2.5 py-1 text-xs text-foreground"
                  >
                    {etiquetaAccion(accion)}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                En este estado el servidor no admite cambios.
              </p>
            )}
          </div>

          {vistaPreviaAvance ? (
            <VistaPreviaAvancePanel vistaPrevia={vistaPreviaAvance} />
          ) : null}

          {vistaPreviaCorreccion ? (
            <VistaPreviaCorreccionPanel vistaPrevia={vistaPreviaCorreccion} />
          ) : null}

          <p className="text-caption text-muted-foreground">
            Versión del recurso: {encuentro.version}. Un cambio con una versión
            anterior se rechaza y no se escribe nada.
          </p>
        </div>

        <SheetFooter>
          <Button
            variant="outline"
            className="min-h-11 w-full"
            onClick={() => onOpenChange(false)}
          >
            Cerrar
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
