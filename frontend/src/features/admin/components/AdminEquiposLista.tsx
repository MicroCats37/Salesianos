"use client";

import { Trophy } from "lucide-react";
import { useMemo } from "react";
import { useAdminCatalogos } from "../hooks/useAdminCatalogos";
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import { useAdminEquipos } from "../hooks/useAdminEquipos";
import type { AdminEquipoListItem } from "../schemas";
import {
  estadoEquipoLabel,
  estadoEquipoTone,
  rosterLabel,
  rosterTone,
} from "../utils/admin.estado.utils";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_EQUIPOS,
  ORDEN_POR_DEFECTO_EQUIPOS,
} from "../utils/admin.orden.utils";
import { formatearFecha } from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import { AdminFiltroSelect } from "./AdminFiltroSelect";
import { type AdminColumna, AdminListaOperativa } from "./AdminListaOperativa";
import { AdminPageHeader } from "./AdminPageHeader";

/**
 * AdminEquiposLista — the teams table (A7).
 *
 * The completeness of a roster (COMPLETO / INCOMPLETO) is DERIVED on the
 * server: the client never compares `jugadores_registrados` with
 * `minimo_deportivo` to decide it.
 */
export function AdminEquiposLista() {
  const control = useAdminControlLista();
  const catalogos = useAdminCatalogos();
  const consulta = useAdminEquipos(control.estado);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(() => adminOpcionesOrdering(ORDEN_EQUIPOS), []);
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminEquipoListItem>[] = [
    {
      clave: "equipo",
      etiqueta: "Equipo",
      render: (item) => (
        <span className="font-black text-slate-900">{item.nombre}</span>
      ),
    },
    {
      clave: "disciplina",
      etiqueta: "Disciplina",
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-bold text-slate-800">
            {item.disciplina_sigla}
          </span>
          <span className="text-[11px] text-slate-500">
            {item.disciplina_nombre}
          </span>
        </div>
      ),
    },
    {
      clave: "categoria",
      etiqueta: "Categoría",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {item.categoria_nombre ?? "—"}
        </span>
      ),
    },
    {
      clave: "inscripcion",
      etiqueta: "Inscripción",
      render: (item) => (
        <span className="text-xs text-slate-600">{item.inscripcion_ref}</span>
      ),
    },
    {
      clave: "roster",
      etiqueta: "Plantilla",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {item.jugadores_registrados}/{item.minimo_deportivo}
        </span>
      ),
    },
    {
      clave: "estado_roster",
      etiqueta: "Completitud",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={rosterLabel(item.estado_roster)}
          tono={rosterTone(item.estado_roster)}
        />
      ),
    },
    {
      clave: "estado",
      etiqueta: "Estado",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={estadoEquipoLabel(item.estado)}
          tono={estadoEquipoTone(item.estado)}
        />
      ),
    },
    {
      clave: "creada",
      etiqueta: "Creada",
      render: (item) => (
        <span className="text-slate-600">
          {formatearFecha(item.created_at)}
        </span>
      ),
    },
  ];

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  return (
    <>
      <AdminPageHeader
        eyebrow="Administración operativa"
        title="Equipos"
        description="Equipos del evento activo con su disciplina, su categoría y la completitud de su plantilla."
        icon={Trophy}
        size="compact"
      />

      <div className="mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6 lg:px-10">
        <AdminListaOperativa
          items={items}
          total={datos?.total ?? 0}
          pagina={datos?.page ?? control.estado.page}
          totalPaginas={datos?.total_pages ?? 1}
          pageSize={datos?.page_size ?? control.estado.pageSize}
          cargando={consulta.isPending}
          error={consulta.error?.message ?? null}
          onReintentar={() => {
            void consulta.refetch();
          }}
          hayFiltros={control.hayFiltros}
          filtrosActivos={control.contadorFiltros}
          onLimpiarFiltros={control.onLimpiarFiltros}
          onCambiarPagina={control.onCambiarPagina}
          onCambiarPageSize={control.onCambiarPageSize}
          termino={control.estado.q}
          onBuscar={control.onBuscar}
          orden={control.estado.ordering || ORDEN_POR_DEFECTO_EQUIPOS}
          opcionesOrden={opcionesOrden}
          onCambiarOrden={control.onCambiarOrden}
          controles={
            <>
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
                etiqueta="Estado"
                valor={control.estado.filtros.estado ?? ""}
                opciones={(catalogo?.estados.equipo ?? []).map((valor) => ({
                  valor,
                  etiqueta: estadoEquipoLabel(valor),
                }))}
                onChange={(valor) => control.onFiltro("estado", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Plantilla"
                valor={control.estado.filtros.roster ?? ""}
                opciones={[
                  { valor: "COMPLETO", etiqueta: "Completo" },
                  { valor: "INCOMPLETO", etiqueta: "Incompleto" },
                ]}
                onChange={(valor) => control.onFiltro("roster", valor)}
              />
            </>
          }
          columnas={columnas}
          claveItem={(item) => item.id}
          renderTarjeta={(item) => (
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col">
                  <span className="text-sm font-black text-slate-900">
                    {item.nombre}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {item.disciplina_sigla} · {item.categoria_nombre ?? "—"} ·{" "}
                    {item.inscripcion_ref}
                  </span>
                </div>
                <AdminEstadoBadge
                  etiqueta={rosterLabel(item.estado_roster)}
                  tono={rosterTone(item.estado_roster)}
                />
              </div>
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  Plantilla {item.jugadores_registrados}/{item.minimo_deportivo}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  {estadoEquipoLabel(item.estado)}
                </span>
              </div>
            </div>
          )}
          tituloVacio="Todavía no hay equipos"
          descripcionVacia="No hay equipos registrados en el evento activo."
        />
      </div>
    </>
  );
}
