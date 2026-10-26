"use client";

import { Swords } from "lucide-react";
import Link from "next/link";
import {
  AdminAccessDenied,
  AdminEstadoBadge,
  AdminPageHeader,
} from "@/features/admin/components";
import { useCompetenciaDetalle } from "../hooks";
import {
  estadoCompetenciaLabel,
  estadoCompetenciaTone,
  estadoEquipoCompetenciaLabel,
  estadoEquipoCompetenciaTone,
  estadoRondaLabel,
  estadoRondaTone,
} from "../utils/competencias.estado.utils";
import { resolverEstadoVista } from "../utils/competencias.vista.utils";
import { CompetenciasEditores } from "./CompetenciasEditores";
import {
  CompetenciasEnlaceCuadro,
  CompetenciasSubnav,
} from "./CompetenciasSubnav";

export interface CompetenciasDetalleProps {
  /** Identifier of the competition of the route. */
  competenciaId: string;
}

/**
 * CompetenciasDetalle — the detail of ONE competition.
 *
 * The page resolves the identifier and the feature owns the data: the teams
 * and the rounds are rendered exactly as the backend returns them, without
 * inventing a participant nor an advance.
 */
export function CompetenciasDetalle({
  competenciaId,
}: CompetenciasDetalleProps) {
  const consulta = useCompetenciaDetalle(competenciaId);

  const detalle = consulta.data?.success ? consulta.data.data : null;

  const estadoVista = resolverEstadoVista({
    cargando: consulta.isPending,
    error: consulta.error?.message ?? null,
    total: detalle ? 1 : 0,
  });

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  return (
    <>
      <AdminPageHeader
        eyebrow="Administración operativa"
        title={detalle?.nombre ?? "Competencia"}
        description={
          detalle
            ? `Competencia del ${detalle.fecha} con ${detalle.total_equipos} equipos y ${detalle.total_encuentros} encuentros.`
            : "Detalle de una competencia del evento activo."
        }
        icon={Swords}
        size="compact"
        badges={
          detalle ? (
            <AdminEstadoBadge
              etiqueta={estadoCompetenciaLabel(detalle.estado)}
              tono={estadoCompetenciaTone(detalle.estado)}
            />
          ) : null
        }
        actions={
          detalle ? (
            <CompetenciasEnlaceCuadro competenciaId={detalle.id} />
          ) : null
        }
      />

      <CompetenciasSubnav />

      <div className="mx-auto w-full max-w-7xl space-y-4 px-4 pb-8 sm:px-6 lg:px-10">
        {estadoVista === "cargando" ? (
          <div className="card-elevated space-y-3 p-6">
            <div className="h-5 w-1/3 animate-pulse rounded-[20px] bg-muted" />
            <div className="h-4 w-2/3 animate-pulse rounded-[20px] bg-muted" />
          </div>
        ) : null}

        {estadoVista === "error" ? (
          <div className="card-elevated space-y-3 p-6 text-center">
            <p className="text-sm font-medium text-destructive">
              {consulta.error?.message ?? "Error al cargar los datos"}
            </p>
            <button
              type="button"
              onClick={() => {
                void consulta.refetch();
              }}
              className="text-xs font-black uppercase tracking-wider text-[#312e8e] hover:underline"
            >
              Reintentar
            </button>
          </div>
        ) : null}

        {estadoVista === "listo" && detalle ? (
          <>
            {/* Equipos — the MANUAL order of the administrator. */}
            <section className="card-elevated overflow-hidden">
              <header className="border-b border-slate-100 px-4 py-3">
                <h2 className="text-sm font-black text-slate-900">
                  Equipos ({detalle.equipos.length})
                </h2>
                <p className="text-[11px] text-slate-500">
                  El orden es el manual del administrador: el sistema nunca lo
                  elige.
                </p>
              </header>

              {detalle.equipos.length === 0 ? (
                <p className="px-4 py-6 text-center text-xs text-slate-500">
                  Todavía no hay equipos en esta competencia.
                </p>
              ) : (
                <ul className="divide-y divide-slate-50">
                  {detalle.equipos.map((equipo) => (
                    <li
                      key={equipo.id}
                      className="flex items-center justify-between gap-3 px-4 py-3"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#312e8e]/10 text-[11px] font-black text-[#312e8e]">
                          {equipo.orden}
                        </span>
                        <span className="truncate text-xs font-bold text-slate-800">
                          {equipo.equipo_nombre}
                        </span>
                      </div>
                      <AdminEstadoBadge
                        etiqueta={estadoEquipoCompetenciaLabel(equipo.estado)}
                        tono={estadoEquipoCompetenciaTone(equipo.estado)}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Rondas — the columns of the bracket. */}
            <section className="card-elevated overflow-hidden">
              <header className="border-b border-slate-100 px-4 py-3">
                <h2 className="text-sm font-black text-slate-900">
                  Rondas ({detalle.rondas.length})
                </h2>
                <p className="text-[11px] text-slate-500">
                  Las rondas que existen se muestran tal como son: un cuadro
                  vacío o parcial sigue siendo legible.
                </p>
              </header>

              {detalle.rondas.length === 0 ? (
                <p className="px-4 py-6 text-center text-xs text-slate-500">
                  Todavía no hay rondas en esta competencia.
                </p>
              ) : (
                <ul className="divide-y divide-slate-50">
                  {detalle.rondas.map((ronda) => (
                    <li
                      key={ronda.id}
                      className="flex items-center justify-between gap-3 px-4 py-3"
                    >
                      <div className="flex min-w-0 flex-col">
                        <span className="truncate text-xs font-bold text-slate-800">
                          {ronda.etiqueta}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {ronda.total_encuentros} encuentros
                        </span>
                      </div>
                      <AdminEstadoBadge
                        etiqueta={estadoRondaLabel(ronda.estado)}
                        tono={estadoRondaTone(ronda.estado)}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <p className="text-center text-[11px] text-slate-500">
              <Link
                href="/administracion/competencias"
                className="font-black uppercase tracking-wider hover:underline"
              >
                Volver a las competencias
              </Link>
            </p>

            {/* La administración del cuadro: semilla, rondas y encuentros. */}
            <CompetenciasEditores detalle={detalle} />
          </>
        ) : null}
      </div>
    </>
  );
}
