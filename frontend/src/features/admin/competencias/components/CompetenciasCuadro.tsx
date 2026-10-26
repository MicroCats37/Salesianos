"use client";

import { GitBranch } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AdminAccessDenied,
  AdminEstadoBadge,
  AdminPageHeader,
} from "@/features/admin/components";
import { useCompetenciaCuadro, useCompetenciasLista } from "../hooks";
import {
  type CompetenciaCuadroCelda,
  type CompetenciaCuadroColumna,
  competenciaCuadroColumnas,
} from "../utils/competencias.mapa.utils";
import { resolverEstadoVista } from "../utils/competencias.vista.utils";
import { CompetenciasAccionesEncuentro } from "./CompetenciasAccionesEncuentro";
import { CompetenciasSubnav } from "./CompetenciasSubnav";

/**
 * CompetenciasCuadro — the bracket of ONE competition.
 *
 * The competition lives in the URL (`?id=`), so the bracket can be shared
 * and reloaded without losing its context.
 *
 * The bracket is a GRID of columns (one column per round) and it NEVER
 * invents a participant nor an advance: a round without encounters and a
 * slot without a team are rendered as they are.
 */
export function CompetenciasCuadro() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const competenciaId = searchParams.get("id") ?? "";

  const lista = useCompetenciasLista({});
  const consulta = useCompetenciaCuadro(competenciaId);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const filas = lista.data?.success ? (lista.data.data ?? []) : [];

  const estadoVista = resolverEstadoVista({
    cargando: consulta.isPending,
    error: consulta.error?.message ?? null,
    total: datos ? 1 : 0,
  });

  function seleccionar(id: string) {
    const parametros = new URLSearchParams(searchParams.toString());
    if (id) {
      parametros.set("id", id);
    } else {
      parametros.delete("id");
    }
    const query = parametros.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  const columnas: CompetenciaCuadroColumna[] = datos
    ? competenciaCuadroColumnas(datos.rondas)
    : [];

  return (
    <>
      <AdminPageHeader
        eyebrow="Administración operativa"
        title="Cuadro"
        description={
          datos
            ? `Cuadro de ${datos.nombre} · ${datos.total_equipos} equipos.`
            : "Elige una competencia para ver su cuadro."
        }
        icon={GitBranch}
        size="compact"
      />

      <CompetenciasSubnav />

      <div className="mx-auto w-full max-w-7xl space-y-4 px-4 pb-8 sm:px-6 lg:px-10">
        <div className="card-elevated p-4">
          <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
            <GitBranch className="size-3" />
            Competencia
          </span>
          <Select
            value={competenciaId || "__todas__"}
            onValueChange={(valor) =>
              seleccionar(valor === "__todas__" ? "" : valor)
            }
          >
            <SelectTrigger
              className="h-9 w-full min-w-[16rem] rounded-xl bg-white text-xs font-bold"
              aria-label="Competencia"
            >
              <SelectValue placeholder="Elige una competencia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__todas__">Elige una competencia</SelectItem>
              {filas.map((competencia) => (
                <SelectItem key={competencia.id} value={competencia.id}>
                  {competencia.nombre} · {competencia.fecha}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {!competenciaId ? (
          <div className="card-elevated px-4 py-10 text-center">
            <p className="text-sm font-medium text-foreground">
              Todavía no hay un cuadro seleccionado
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Elige una competencia o abre el cuadro desde la lista.
            </p>
            <Link
              href="/administracion/competencias"
              className="mt-3 inline-block text-xs font-black uppercase tracking-wider text-[#312e8e] hover:underline"
            >
              Ver las competencias
            </Link>
          </div>
        ) : null}

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

        {estadoVista === "listo" && datos ? (
          columnas.length === 0 ? (
            <div className="card-elevated px-4 py-10 text-center">
              <p className="text-sm font-medium text-foreground">
                El cuadro todavía está vacío
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                La competencia no tiene rondas: nada se inventa y nada se
                autocompleta.
              </p>
            </div>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-4">
              {columnas.map((columna) => (
                <section
                  key={columna.id}
                  aria-label={columna.etiqueta}
                  className="w-64 shrink-0"
                >
                  <header className="mb-3 flex items-center justify-between gap-2">
                    <h2 className="truncate text-xs font-black uppercase tracking-wider text-slate-900">
                      {columna.etiqueta}
                    </h2>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {columna.estado}
                    </span>
                  </header>

                  <div className="space-y-3">
                    {columna.celdas.length === 0 ? (
                      <p className="card-elevated px-3 py-6 text-center text-[11px] text-slate-500">
                        Sin encuentros
                      </p>
                    ) : (
                      columna.celdas.map((celda) => (
                        <CeldaCuadro
                          key={celda.encuentro.id}
                          celda={celda}
                          competenciaId={datos.competencia_id}
                          fechaCompetencia={datos.fecha}
                        />
                      ))
                    )}
                  </div>
                </section>
              ))}
            </div>
          )
        ) : null}
      </div>
    </>
  );
}

/** One cell of the bracket: ONE encounter with its two slots. */
function CeldaCuadro({
  celda,
  competenciaId,
  fechaCompetencia,
}: {
  celda: CompetenciaCuadroCelda;
  competenciaId: string;
  fechaCompetencia: string;
}) {
  return (
    <article className="card-elevated space-y-2 p-3">
      <div className="flex items-start justify-between gap-2">
        <span className="text-[11px] font-black uppercase tracking-wider text-slate-400">
          {celda.encuentro.ronda_etiqueta ?? `Orden ${celda.encuentro.orden}`}
        </span>
        {celda.esBye ? (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-slate-600">
            Bye
          </span>
        ) : null}
      </div>

      <div className="space-y-1">
        <p
          className={
            celda.encuentro.ganador_id === celda.encuentro.participante_1_id
              ? "text-xs font-black text-slate-900"
              : "text-xs font-bold text-slate-700"
          }
        >
          {celda.participante1}
        </p>
        <p
          className={
            celda.encuentro.ganador_id === celda.encuentro.participante_2_id
              ? "text-xs font-black text-slate-900"
              : "text-xs font-bold text-slate-700"
          }
        >
          {celda.participante2}
        </p>
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-slate-50 pt-2">
        <span className="text-[11px] text-slate-500">{celda.marcador}</span>
        <AdminEstadoBadge etiqueta={celda.estado} tono={celda.tono} />
      </div>

      {celda.tieneHorario ? (
        <p className="text-[10px] uppercase tracking-wider text-slate-400">
          {celda.encuentro.inicio_programado?.slice(11, 16)} –{" "}
          {celda.encuentro.fin_programado?.slice(11, 16)}
        </p>
      ) : null}

      {/* La administración del encuentro: horario, bye, enlace y resultado. */}
      <CompetenciasAccionesEncuentro
        competenciaId={competenciaId}
        encuentro={celda.encuentro}
        fechaCompetencia={fechaCompetencia}
      />
    </article>
  );
}
