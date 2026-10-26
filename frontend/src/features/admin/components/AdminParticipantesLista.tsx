"use client";

import { Users } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAdminCatalogos } from "../hooks/useAdminCatalogos";
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import {
  useAdminParticipaciones,
  useAdminParticipantes,
} from "../hooks/useAdminParticipantes";
import type {
  AdminParticipacionListItem,
  AdminParticipanteListItem,
} from "../schemas";
import {
  estadoParticipacionLabel,
  estadoPersonaLabel,
  estadoPoolLabel,
  estadoPoolTone,
  rolParticipanteLabel,
} from "../utils/admin.estado.utils";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_PARTICIPACIONES,
  ORDEN_PARTICIPANTES,
  ORDEN_POR_DEFECTO_PARTICIPACIONES,
  ORDEN_POR_DEFECTO_PARTICIPANTES,
} from "../utils/admin.orden.utils";
import { formatearFecha } from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import { AdminFiltroSelect } from "./AdminFiltroSelect";
import { type AdminColumna, AdminListaOperativa } from "./AdminListaOperativa";
import { AdminPageHeader } from "./AdminPageHeader";

/**
 * NAMESPACES of the two tabs.
 *
 * The people (A8) and the roster rows (A9) are TWO different surfaces with
 * two different filter vocabularies and two different ordering whitelists.
 * Each tab owns its own URL parameters, so a filter of one tab can never be
 * sent to the endpoint of the other one.
 */
const PREFIJO_PARTICIPANTES = "participantes_";
const PREFIJO_PARTICIPACIONES = "participaciones_";

const OTROS_PARTICIPANTES = [PREFIJO_PARTICIPACIONES];
const OTROS_PARTICIPACIONES = [PREFIJO_PARTICIPANTES];

/**
 * AdminParticipantesLista — the people and the roster rows (A8, A9).
 *
 * ONE paid cup authorises a person in EVERY contracted discipline: a person
 * can hold several participations without holding several cupos. The two
 * counters are never interchangeable, so they live in two tabs and the client
 * never reconciles them.
 */
export function AdminParticipantesLista() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const tab =
    searchParams.get("tab") === "participaciones"
      ? "participaciones"
      : "participantes";

  function cambiarTab(nuevo: string) {
    const parametros = new URLSearchParams(searchParams.toString());
    if (nuevo === "participaciones") {
      parametros.set("tab", "participaciones");
    } else {
      parametros.delete("tab");
    }
    const query = parametros.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, {
      scroll: false,
    });
  }

  return (
    <>
      <AdminPageHeader
        eyebrow="Administración operativa"
        title="Participantes"
        description="Las personas registradas en el evento y sus participaciones por disciplina. Un cupo pagado habilita a una persona en todas las disciplinas contratadas: por eso son dos cifras distintas."
        icon={Users}
        size="compact"
      />

      <div className="mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6 lg:px-10">
        <Tabs value={tab} onValueChange={cambiarTab} className="gap-4">
          <div className="overflow-x-auto pb-1">
            <TabsList variant="line" className="w-max gap-4">
              <TabsTrigger
                value="participantes"
                className="px-3 text-xs font-black uppercase tracking-wider"
              >
                Personas registradas
              </TabsTrigger>
              <TabsTrigger
                value="participaciones"
                className="px-3 text-xs font-black uppercase tracking-wider"
              >
                Participaciones por disciplina
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="participantes" className="mt-4">
            <PanelParticipantes />
          </TabsContent>

          <TabsContent value="participaciones" className="mt-4">
            <PanelParticipaciones />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}

/** Tab 1 — the registered people of the pool (A8). */
function PanelParticipantes() {
  const control = useAdminControlLista(
    PREFIJO_PARTICIPANTES,
    OTROS_PARTICIPANTES,
  );
  const catalogos = useAdminCatalogos();
  const consulta = useAdminParticipantes(control.estado);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(
    () => adminOpcionesOrdering(ORDEN_PARTICIPANTES),
    [],
  );
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminParticipanteListItem>[] = [
    {
      clave: "persona",
      etiqueta: "Persona",
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-black text-slate-900">
            {item.persona_nombre}
          </span>
          <span className="text-[11px] text-slate-500">
            {item.persona_documento}
          </span>
        </div>
      ),
    },
    {
      clave: "estado",
      etiqueta: "Estado",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {estadoPersonaLabel(item.estado)}
        </span>
      ),
    },
    {
      clave: "estado_pool",
      etiqueta: "Estado pool",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={estadoPoolLabel(item.estado_pool)}
          tono={estadoPoolTone(item.estado_pool)}
        />
      ),
    },
    {
      clave: "cupo",
      etiqueta: "Cupo activo",
      render: (item) => (
        <span className="text-xs font-bold text-slate-800">
          {item.tiene_cupo_activo ? "Sí" : "No"}
        </span>
      ),
    },
    {
      clave: "disciplinas",
      etiqueta: "Disciplinas",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {item.disciplinas.length > 0 ? item.disciplinas.join(", ") : "—"}
        </span>
      ),
    },
    {
      clave: "motivo",
      etiqueta: "Motivo de bloqueo",
      render: (item) => (
        <span className="text-[11px] text-slate-500">
          {item.motivo_bloqueo ?? "—"}
        </span>
      ),
    },
    {
      clave: "creada",
      etiqueta: "Registrada",
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
      orden={control.estado.ordering || ORDEN_POR_DEFECTO_PARTICIPANTES}
      opcionesOrden={opcionesOrden}
      onCambiarOrden={control.onCambiarOrden}
      controles={
        <>
          <AdminFiltroSelect
            etiqueta="Estado pool"
            valor={control.estado.filtros.estado_pool ?? ""}
            opciones={(catalogo?.estados.pool ?? []).map((valor) => ({
              valor,
              etiqueta: estadoPoolLabel(valor),
            }))}
            onChange={(valor) => control.onFiltro("estado_pool", valor)}
          />
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
            etiqueta="Cupo activo"
            valor={control.estado.filtros.con_cupo ?? ""}
            opciones={[
              { valor: "true", etiqueta: "Con cupo" },
              { valor: "false", etiqueta: "Sin cupo" },
            ]}
            onChange={(valor) => control.onFiltro("con_cupo", valor)}
          />
        </>
      }
      columnas={columnas}
      claveItem={(item) => item.inscripcion_persona_id}
      renderTarjeta={(item) => (
        <div className="space-y-2">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col">
              <span className="text-sm font-black text-slate-900">
                {item.persona_nombre}
              </span>
              <span className="text-[11px] text-slate-500">
                {item.persona_documento}
              </span>
            </div>
            <AdminEstadoBadge
              etiqueta={estadoPoolLabel(item.estado_pool)}
              tono={estadoPoolTone(item.estado_pool)}
            />
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {estadoPersonaLabel(item.estado)}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-1">
              Cupo {item.tiene_cupo_activo ? "activo" : "sin cupo"}
            </span>
            {item.disciplinas.length > 0 && (
              <span className="rounded-full bg-slate-100 px-2 py-1">
                {item.disciplinas.join(" · ")}
              </span>
            )}
          </div>
        </div>
      )}
      tituloVacio="Todavía no hay participantes"
      descripcionVacia="No hay personas registradas en el evento activo."
    />
  );
}

/** Tab 2 — the roster rows (A9). */
function PanelParticipaciones() {
  const control = useAdminControlLista(
    PREFIJO_PARTICIPACIONES,
    OTROS_PARTICIPACIONES,
  );
  const catalogos = useAdminCatalogos();
  const consulta = useAdminParticipaciones(control.estado);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(
    () => adminOpcionesOrdering(ORDEN_PARTICIPACIONES),
    [],
  );
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminParticipacionListItem>[] = [
    {
      clave: "persona",
      etiqueta: "Persona",
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-black text-slate-900">
            {item.persona_nombre}
          </span>
          <span className="text-[11px] text-slate-500">
            {item.persona_documento}
          </span>
        </div>
      ),
    },
    {
      clave: "equipo",
      etiqueta: "Equipo",
      render: (item) => (
        <span className="font-bold text-slate-800">{item.equipo_nombre}</span>
      ),
    },
    {
      clave: "disciplina",
      etiqueta: "Disciplina",
      render: (item) => (
        <span className="text-xs text-slate-600">{item.disciplina_sigla}</span>
      ),
    },
    {
      clave: "rol",
      etiqueta: "Rol",
      render: (item) => (
        <span className="text-xs font-bold text-slate-800">
          {rolParticipanteLabel(item.rol)}
        </span>
      ),
    },
    {
      clave: "talla",
      etiqueta: "Talla",
      render: (item) => (
        <span className="text-xs text-slate-600">{item.talla_camiseta}</span>
      ),
    },
    {
      clave: "estado",
      etiqueta: "Estado",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {estadoParticipacionLabel(item.estado)}
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
      orden={control.estado.ordering || ORDEN_POR_DEFECTO_PARTICIPACIONES}
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
            etiqueta="Rol"
            valor={control.estado.filtros.rol ?? ""}
            opciones={(catalogo?.estados.rol_participante ?? []).map(
              (valor) => ({
                valor,
                etiqueta: rolParticipanteLabel(valor),
              }),
            )}
            onChange={(valor) => control.onFiltro("rol", valor)}
          />
          <AdminFiltroSelect
            etiqueta="Estado"
            valor={control.estado.filtros.estado ?? ""}
            opciones={[
              { valor: "A", etiqueta: "Activa" },
              { valor: "R", etiqueta: "Retirada" },
            ]}
            onChange={(valor) => control.onFiltro("estado", valor)}
          />
        </>
      }
      columnas={columnas}
      claveItem={(item) => item.id}
      renderTarjeta={(item) => (
        <div className="space-y-2">
          <div className="flex flex-col">
            <span className="text-sm font-black text-slate-900">
              {item.persona_nombre}
            </span>
            <span className="text-[11px] text-slate-500">
              {item.persona_documento}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {item.equipo_nombre}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {item.disciplina_sigla}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {rolParticipanteLabel(item.rol)}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {estadoParticipacionLabel(item.estado)}
            </span>
          </div>
        </div>
      )}
      tituloVacio="Todavía no hay participaciones"
      descripcionVacia="No hay personas asignadas a equipos en el evento activo."
    />
  );
}
