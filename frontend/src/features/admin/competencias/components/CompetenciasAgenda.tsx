"use client";

import { CalendarDays } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  AdminAccessDenied,
  AdminEstadoBadge,
  AdminFiltroSelect,
  AdminPageHeader,
} from "@/features/admin/components";
import {
  useAdminCatalogos,
  useAdminControlLista,
} from "@/features/admin/hooks";
import { useAgendaCompetencias } from "../hooks";
import {
  ENCUENTRO_ESTADOS,
  estadoEncuentroLabel,
} from "../utils/competencias.estado.utils";
import {
  type AgendaFranja,
  competenciaAgendaFranjas,
} from "../utils/competencias.mapa.utils";
import { competenciasParametrosAgenda } from "../utils/competencias.url.utils";
import {
  resolverEstadoVista,
  resolverVistaVacio,
} from "../utils/competencias.vista.utils";
import { CompetenciasFiltros } from "./CompetenciasFiltros";
import { CompetenciasSubnav } from "./CompetenciasSubnav";

/**
 * CompetenciasAgenda — the TEMPORAL agenda of ONE day.
 *
 * The day lives in the URL, so the agenda can be shared and reloaded without
 * losing its context. The backend resolves the day itself when the client
 * does not say which one it wants: the answer always carries the resolved
 * day.
 *
 * The agenda is a LIST of the encounters of the day, grouped by the instant
 * they start.
 */
export function CompetenciasAgenda() {
  const control = useAdminControlLista();
  const catalogos = useAdminCatalogos();

  const consulta = useAgendaCompetencias(
    competenciasParametrosAgenda(control.estado.filtros),
  );

  const datos = consulta.data?.success ? consulta.data.data : null;
  const encuentros = datos?.encuentros ?? [];

  const estadoVista = resolverEstadoVista({
    cargando: consulta.isPending,
    error: consulta.error?.message ?? null,
    total: encuentros.length,
  });

  const vacio = resolverVistaVacio(
    control.hayFiltros,
    "La agenda de este día está vacía",
    "No hay encuentros programados para este día.",
  );

  const catalogo = catalogos.data?.success ? catalogos.data.data : null;
  const franjas: AgendaFranja[] = competenciaAgendaFranjas(encuentros);

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  return (
    <>
      <AdminPageHeader
        eyebrow="Administración operativa"
        title="Agenda"
        description={
          datos
            ? `Encuentros del ${datos.fecha} · ${datos.total} en total.`
            : "Los encuentros programados de un día, en orden temporal."
        }
        icon={CalendarDays}
        size="compact"
      />

      <CompetenciasSubnav />

      <div className="mx-auto w-full max-w-7xl space-y-4 px-4 pb-8 sm:px-6 lg:px-10">
        <CompetenciasFiltros
          hayFiltros={control.hayFiltros}
          filtrosActivos={control.contadorFiltros}
          onLimpiarFiltros={control.onLimpiarFiltros}
          controles={
            <>
              <div>
                <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                  <CalendarDays className="size-3" />
                  Día
                </span>
                <Input
                  type="date"
                  value={control.estado.filtros.fecha ?? ""}
                  onChange={(evento) =>
                    control.onFiltro("fecha", evento.target.value)
                  }
                  aria-label="Día de la agenda"
                  className="h-9 rounded-xl bg-white text-xs font-medium"
                />
              </div>
              <AdminFiltroSelect
                etiqueta="Disciplina"
                valor={control.estado.filtros.disciplina_id ?? ""}
                opciones={(catalogo?.disciplinas ?? []).map((disciplina) => ({
                  valor: disciplina.id,
                  etiqueta: disciplina.sigla
                    ? `${disciplina.sigla} · ${disciplina.nombre}`
                    : disciplina.nombre,
                }))}
                onChange={(valor) => control.onFiltro("disciplina_id", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Categoría"
                valor={control.estado.filtros.categoria_id ?? ""}
                opciones={(catalogo?.categorias ?? []).map((categoria) => ({
                  valor: categoria.id,
                  etiqueta: categoria.nombre,
                }))}
                onChange={(valor) => control.onFiltro("categoria_id", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Estado"
                valor={control.estado.filtros.estado ?? ""}
                opciones={ENCUENTRO_ESTADOS.map((estado) => ({
                  valor: estado,
                  etiqueta: estadoEncuentroLabel(estado),
                }))}
                onChange={(valor) => control.onFiltro("estado", valor)}
              />
            </>
          }
        />

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

        {estadoVista === "vacio" ? (
          <div className="card-elevated px-4 py-10 text-center">
            <p className="text-sm font-medium text-foreground">
              {vacio.titulo}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {vacio.descripcion}
            </p>
            {vacio.accion ? (
              <button
                type="button"
                onClick={control.onLimpiarFiltros}
                className="mt-3 text-xs font-black uppercase tracking-wider text-[#312e8e] hover:underline"
              >
                {vacio.accion}
              </button>
            ) : null}
          </div>
        ) : null}

        {estadoVista === "listo" ? (
          <div className="space-y-4">
            {franjas.map((franja) => (
              <section key={franja.clave} className="space-y-2">
                <h2 className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-500">
                  <span className="size-2 rounded-full bg-[#312e8e]" />
                  {franja.etiqueta}
                </h2>

                <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {franja.encuentros.map((fila) => (
                    <li key={fila.encuentro.id} className="card-elevated p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="truncate text-[11px] font-bold uppercase tracking-wider text-slate-500">
                            {fila.competencia}
                          </p>
                          <p className="mt-1 text-sm font-black text-slate-900">
                            {fila.participantes.length > 0
                              ? fila.participantes.join(" vs ")
                              : "Por definir"}
                          </p>
                        </div>
                        <AdminEstadoBadge
                          etiqueta={fila.estado}
                          tono={fila.tono}
                        />
                      </div>

                      <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-600">
                        <span className="rounded-full bg-slate-100 px-2 py-1">
                          {fila.horario}
                        </span>
                        {fila.duracionMinutos !== null ? (
                          <span className="rounded-full bg-slate-100 px-2 py-1">
                            {fila.duracionMinutos} min
                          </span>
                        ) : null}
                        {fila.esBye ? (
                          <span className="rounded-full bg-slate-100 px-2 py-1">
                            Bye
                          </span>
                        ) : null}
                        {fila.marcador !== "—" ? (
                          <span className="rounded-full bg-slate-100 px-2 py-1">
                            {fila.marcador}
                          </span>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        ) : null}
      </div>
    </>
  );
}
