"use client";

import { ClipboardList } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo } from "react";
import { useAdminCatalogos } from "../hooks/useAdminCatalogos";
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import { useAdminInscripciones } from "../hooks/useAdminInscripciones";
import type { AdminInscripcionListItem } from "../schemas";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_INSCRIPCIONES,
  ORDEN_POR_DEFECTO_INSCRIPCIONES,
} from "../utils/admin.orden.utils";
import {
  estadoInscripcionLabel,
  estadoInscripcionTone,
  formatearFecha,
  formatearMonto,
} from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import { AdminFiltroSelect } from "./AdminFiltroSelect";
import { type AdminColumna, AdminListaOperativa } from "./AdminListaOperativa";
import { AdminPageHeader } from "./AdminPageHeader";

/**
 * AdminInscripcionesLista — the registrations table (A3).
 *
 * PEOPLE and ROSTER ROWS are two different numbers and the table shows them
 * as two different columns: `personas` is the distinct registered people and
 * `participaciones` is the roster rows. One paid cup authorises a person in
 * every contracted discipline, so the two are never interchangeable and the
 * client never reconciles them.
 */
export function AdminInscripcionesLista() {
  const router = useRouter();
  const control = useAdminControlLista();
  const catalogos = useAdminCatalogos();
  const consulta = useAdminInscripciones(control.estado);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(
    () => adminOpcionesOrdering(ORDEN_INSCRIPCIONES),
    [],
  );

  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminInscripcionListItem>[] = [
    {
      clave: "responsable",
      etiqueta: "Responsable",
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-black text-slate-900">
            {item.responsable_nombre}
          </span>
          <span className="text-[11px] text-slate-500">
            {item.responsable_documento}
          </span>
        </div>
      ),
    },
    {
      clave: "paquete",
      etiqueta: "Paquete",
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-bold text-slate-800">
            {item.paquete_nombre}
          </span>
          <span className="text-[11px] text-slate-500">
            {item.promocion_nombre}
          </span>
        </div>
      ),
    },
    {
      clave: "estado",
      etiqueta: "Estado",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={estadoInscripcionLabel(item.estado)}
          tono={estadoInscripcionTone(item.estado)}
        />
      ),
    },
    {
      clave: "equipos",
      etiqueta: "Equipos",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {item.equipos_completos}/{item.equipos_total}
        </span>
      ),
    },
    {
      clave: "personas",
      etiqueta: "Personas",
      render: (item) => (
        <span className="font-bold text-slate-800">{item.personas}</span>
      ),
    },
    {
      clave: "participaciones",
      etiqueta: "Participaciones",
      render: (item) => (
        <span className="font-bold text-slate-800">{item.participaciones}</span>
      ),
    },
    {
      clave: "cupos",
      etiqueta: "Cupos pagados",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {item.cupos_pagados}/{item.cupos_contratados}
        </span>
      ),
    },
    {
      clave: "monto",
      etiqueta: "Monto pagado",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {formatearMonto(item.monto_pagado)}
        </span>
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
        title="Inscripciones"
        description="Cada inscripción del evento activo con su responsable, su paquete, sus equipos, sus personas, sus participaciones y su saldo de cupos. Los conteos los calcula el servidor."
        icon={ClipboardList}
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
          orden={control.estado.ordering || ORDEN_POR_DEFECTO_INSCRIPCIONES}
          opcionesOrden={opcionesOrden}
          onCambiarOrden={control.onCambiarOrden}
          controles={
            <>
              <AdminFiltroSelect
                etiqueta="Estado"
                valor={control.estado.filtros.estado ?? ""}
                opciones={(catalogo?.estados.inscripcion ?? []).map(
                  (valor) => ({
                    valor,
                    etiqueta: estadoInscripcionLabel(valor),
                  }),
                )}
                onChange={(valor) => control.onFiltro("estado", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Paquete"
                valor={control.estado.filtros.paquete_id ?? ""}
                opciones={(catalogo?.paquetes ?? []).map((paquete) => ({
                  valor: paquete.id,
                  etiqueta: paquete.nombre,
                }))}
                onChange={(valor) => control.onFiltro("paquete_id", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Promoción"
                valor={control.estado.filtros.promocion_id ?? ""}
                opciones={(catalogo?.promociones ?? []).map((promocion) => ({
                  valor: promocion.id,
                  etiqueta: promocion.nombre,
                }))}
                onChange={(valor) => control.onFiltro("promocion_id", valor)}
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
                    {item.responsable_nombre}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {item.responsable_documento} · {item.paquete_nombre}
                  </span>
                </div>
                <AdminEstadoBadge
                  etiqueta={estadoInscripcionLabel(item.estado)}
                  tono={estadoInscripcionTone(item.estado)}
                />
              </div>
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  Equipos {item.equipos_completos}/{item.equipos_total}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  Personas {item.personas}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  Participaciones {item.participaciones}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  Cupos {item.cupos_pagados}/{item.cupos_contratados}
                </span>
              </div>
            </div>
          )}
          onAbrir={(item) => {
            router.push(`/administracion/inscripciones/${item.id}`);
          }}
          tituloVacio="Todavía no hay inscripciones"
          descripcionVacia="No se ha registrado ninguna inscripción en el evento activo."
        />
      </div>
    </>
  );
}
