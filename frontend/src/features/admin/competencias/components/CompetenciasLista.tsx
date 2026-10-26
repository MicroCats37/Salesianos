"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { Swords } from "lucide-react";
import Link from "next/link";
import { AppDataTable } from "@/components-app/tables";
import {
  AdminAccessDenied,
  AdminEstadoBadge,
  AdminFiltroRangoFechas,
  AdminFiltroSelect,
  AdminPageHeader,
} from "@/features/admin/components";
import {
  useAdminCatalogos,
  useAdminControlLista,
} from "@/features/admin/hooks";
import { useCompetenciasLista } from "../hooks";
import type { CompetenciaListaItem } from "../schemas";
import {
  COMPETENCIA_ESTADOS,
  estadoCompetenciaLabel,
  estadoCompetenciaTone,
} from "../utils/competencias.estado.utils";
import { competenciasParametrosLista } from "../utils/competencias.url.utils";
import {
  resolverEstadoVista,
  resolverVistaVacio,
} from "../utils/competencias.vista.utils";
import { CompetenciasFiltros } from "./CompetenciasFiltros";
import {
  CompetenciasEnlaceCuadro,
  CompetenciasSubnav,
} from "./CompetenciasSubnav";

/**
 * CompetenciasLista — the list of the competitions of the administrative
 * scope.
 *
 * The filters live in the URL and the data lives in the TanStack Query
 * cache: the component NEVER fetches and NEVER holds server state
 * (`contract/next-app-architecture-contract.md` §4).
 */
export function CompetenciasLista() {
  const control = useAdminControlLista();
  const catalogos = useAdminCatalogos();

  const consulta = useCompetenciasLista(
    competenciasParametrosLista(control.estado.filtros),
  );

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos ?? [];

  const estadoVista = resolverEstadoVista({
    cargando: consulta.isPending,
    error: consulta.error?.message ?? null,
    total: items.length,
  });

  const vacio = resolverVistaVacio(
    control.hayFiltros,
    "Todavía no hay competencias",
    "No hay competencias registradas en el evento activo.",
  );

  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: ColumnDef<CompetenciaListaItem>[] = [
    {
      id: "competencia",
      header: "Competencia",
      cell: ({ row }) => (
        <div className="flex flex-col">
          <span className="font-black text-slate-900">
            {row.original.nombre}
          </span>
          <span className="text-[11px] text-slate-500">
            {row.original.fecha}
          </span>
        </div>
      ),
    },
    {
      id: "estado",
      header: "Estado",
      cell: ({ row }) => (
        <AdminEstadoBadge
          etiqueta={estadoCompetenciaLabel(row.original.estado)}
          tono={estadoCompetenciaTone(row.original.estado)}
        />
      ),
    },
    {
      id: "equipos",
      header: "Equipos",
      cell: ({ row }) => (
        <span className="font-bold text-slate-800">
          {row.original.total_equipos}
        </span>
      ),
    },
    {
      id: "encuentros",
      header: "Encuentros",
      cell: ({ row }) => (
        <div className="flex flex-col">
          <span className="font-bold text-slate-800">
            {row.original.total_encuentros}
          </span>
          <span className="text-[11px] text-slate-500">
            {row.original.total_encuentros_finalizados} finalizados
          </span>
        </div>
      ),
    },
    {
      id: "acciones",
      header: "",
      cell: ({ row }) => (
        <div className="flex items-center gap-3">
          <Link
            href={`/administracion/competencias/${row.original.id}`}
            className="text-[11px] font-black uppercase tracking-wider text-slate-500 hover:text-slate-800 hover:underline"
          >
            Detalle
          </Link>
          <CompetenciasEnlaceCuadro competenciaId={row.original.id} />
        </div>
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
        title="Competencias"
        description="Competencias del evento activo con sus equipos, sus rondas y su cuadro."
        icon={Swords}
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
                opciones={COMPETENCIA_ESTADOS.map((estado) => ({
                  valor: estado,
                  etiqueta: estadoCompetenciaLabel(estado),
                }))}
                onChange={(valor) => control.onFiltro("estado", valor)}
              />
              <AdminFiltroRangoFechas
                etiqueta="Fecha"
                desde={control.estado.filtros.fecha_desde ?? ""}
                hasta={control.estado.filtros.fecha_hasta ?? ""}
                onChange={(desde, hasta) =>
                  control.onFiltros({
                    fecha_desde: desde,
                    fecha_hasta: hasta,
                  })
                }
              />
            </>
          }
        />

        <AppDataTable
          columns={columnas}
          data={items}
          isLoading={estadoVista === "cargando"}
          isError={estadoVista === "error"}
          onRetry={() => {
            void consulta.refetch();
          }}
          emptyMessage={vacio.titulo}
          emptyDescription={
            estadoVista === "error"
              ? (consulta.error?.message ?? "Error al cargar los datos")
              : vacio.descripcion
          }
          emptyIcon={<Swords className="size-8" aria-hidden="true" />}
          emptyActionLabel={vacio.accion ?? undefined}
          emptyAction={
            vacio.accion ? () => control.onLimpiarFiltros() : undefined
          }
          showPagination={false}
        />
      </div>
    </>
  );
}
