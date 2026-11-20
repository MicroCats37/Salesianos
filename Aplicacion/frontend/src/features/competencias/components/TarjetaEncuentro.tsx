"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ChipEstadoCompetencia } from "./ChipEstadoCompetencia";
import { PanelDetalleEncuentro } from "./PanelDetalleEncuentro";
import { estadoEncuentro } from "../utils/competencias.estados.utils";
import type {
  Encuentro,
  VistaPreviaAvance,
  VistaPreviaCorreccion,
} from "../types/competencia.types";

/**
 * TarjetaEncuentro - the card of an encounter in the bracket.
 *
 * The card IS a button: its accessible name carries BOTH teams and the
 * score ("Colegio Norte 2, Colegio Sur 1"), because a reader who cannot see
 * the card still has to know which encounter it is (`RB-05` ADM-12).
 *
 * It opens THE panel of the area, the same one the list and the agenda use
 * (`GOV-02-RB-05a`): there is one editor of an encounter, never two.
 */
export function TarjetaEncuentro({
  encuentro,
  vistaPreviaAvance,
  vistaPreviaCorreccion,
  conflicto,
  className,
}: {
  encuentro: Encuentro;
  vistaPreviaAvance?: VistaPreviaAvance;
  vistaPreviaCorreccion?: VistaPreviaCorreccion;
  conflicto?: { mensaje: string };
  className?: string;
}) {
  const [abierto, setAbierto] = useState(false);

  const equipo1 = encuentro.participantes.find(
    (p) => p.slot === "PARTICIPANTE_1",
  )?.equipo_nombre;
  const equipo2 = encuentro.participantes.find(
    (p) => p.slot === "PARTICIPANTE_2",
  )?.equipo_nombre;

  const nombre1 = equipo1 ?? "Sin equipo";
  const nombre2 = equipo2 ?? "Sin equipo";

  const marcador1 = encuentro.puntaje_1;
  const marcador2 = encuentro.puntaje_2;

  const nombreAccesible = `${nombre1} ${marcador1 ?? "sin marcador"}, ${nombre2} ${
    marcador2 ?? "sin marcador"
  }`;

  const esGanador1 =
    encuentro.ganador_equipo_id !== null &&
    encuentro.ganador_equipo_id ===
      encuentro.participantes.find((p) => p.slot === "PARTICIPANTE_1")?.equipo_id;
  const esGanador2 =
    encuentro.ganador_equipo_id !== null &&
    encuentro.ganador_equipo_id ===
      encuentro.participantes.find((p) => p.slot === "PARTICIPANTE_2")?.equipo_id;

  return (
    <>
      <button
        type="button"
        onClick={() => setAbierto(true)}
        aria-label={nombreAccesible}
        className={cn(
          "flex w-full flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3 text-left shadow-[var(--elevation-sm)] transition-colors duration-(--motion-duration-fast) hover:border-primary focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
          className,
        )}
      >
        <span className="flex items-center justify-between gap-2">
          <span className="text-caption text-muted-foreground">
            {encuentro.ronda_etiqueta}
          </span>
          <ChipEstadoCompetencia
            estado={estadoEncuentro(encuentro.estado)}
            className="shrink-0"
          />
        </span>

        <span className="flex flex-col gap-1">
          <span className="flex items-center justify-between gap-2">
            <span
              className={cn(
                "truncate text-sm",
                esGanador1
                  ? "font-semibold text-foreground"
                  : "text-foreground",
              )}
            >
              {nombre1}
            </span>
            <span className="text-sm font-semibold text-foreground tabular-nums">
              {marcador1 ?? "—"}
            </span>
          </span>
          <span className="flex items-center justify-between gap-2">
            <span
              className={cn(
                "truncate text-sm",
                esGanador2
                  ? "font-semibold text-foreground"
                  : "text-foreground",
              )}
            >
              {nombre2}
            </span>
            <span className="text-sm font-semibold text-foreground tabular-nums">
              {marcador2 ?? "—"}
            </span>
          </span>
        </span>

        {encuentro.es_bye ? (
          <span className="text-caption text-muted-foreground">Pase libre</span>
        ) : null}
      </button>

      <PanelDetalleEncuentro
        encuentro={encuentro}
        vistaPreviaAvance={vistaPreviaAvance}
        vistaPreviaCorreccion={vistaPreviaCorreccion}
        conflicto={conflicto}
        open={abierto}
        onOpenChange={setAbierto}
      />
    </>
  );
}
