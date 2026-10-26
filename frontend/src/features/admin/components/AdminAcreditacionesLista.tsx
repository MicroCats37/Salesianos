"use client";

import { QrCode } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAdminAccesos,
  useAdminAcreditacionDetalle,
  useAdminAcreditaciones,
} from "../hooks/useAdminAcreditaciones";
import { useAdminCatalogos } from "../hooks/useAdminCatalogos";
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import { useAdminDetalleUrl } from "../hooks/useAdminListaUrl";
import type {
  AdminAccesoListItem,
  AdminAcreditacionListItem,
} from "../schemas";
import {
  autorizacionFiestaLabel,
  autorizacionFiestaTone,
  estadoAcreditacionLabel,
  estadoAcreditacionTone,
  resultadoAccesoLabel,
  resultadoAccesoTone,
} from "../utils/admin.estado.utils";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_ACCESOS,
  ORDEN_ACREDITACIONES,
  ORDEN_POR_DEFECTO_ACCESOS,
  ORDEN_POR_DEFECTO_ACREDITACIONES,
} from "../utils/admin.orden.utils";
import { formatearFecha } from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import { AdminFiltroRangoFechas } from "./AdminFiltroRangoFechas";
import { AdminFiltroSelect } from "./AdminFiltroSelect";
import {
  AdminListaError,
  AdminListaSkeleton,
  AdminListaVacia,
} from "./AdminListaEstados";
import { type AdminColumna, AdminListaOperativa } from "./AdminListaOperativa";
import { AdminPageHeader } from "./AdminPageHeader";

/**
 * NAMESPACES of the two tabs — the accreditations (A10) and the access log
 * (A12) have two different filter vocabularies and two different ordering
 * whitelists.
 */
const PREFIJO_ACREDITACIONES = "acreditaciones_";
const PREFIJO_ACCESOS = "accesos_";

const OTROS_ACREDITACIONES = [PREFIJO_ACCESOS];
const OTROS_ACCESOS = [PREFIJO_ACREDITACIONES];

/**
 * AdminAcreditacionesLista — the accreditations (A10, A11) and the access log
 * (A12).
 *
 * The QR code NEVER travels in a read payload: it is a live bearer
 * credential and it is not even part of the schema of the frontend.
 */
export function AdminAcreditacionesLista() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const tab =
    searchParams.get("tab") === "accesos" ? "accesos" : "acreditaciones";

  function cambiarTab(nuevo: string) {
    const parametros = new URLSearchParams(searchParams.toString());
    if (nuevo === "accesos") {
      parametros.set("tab", "accesos");
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
        title="Acreditaciones y accesos"
        description="Acreditaciones del evento activo y bitácora de los accesos registrados por los lectores. El código QR vivo nunca forma parte de estas respuestas."
        icon={QrCode}
        size="compact"
      />

      <div className="mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6 lg:px-10">
        <Tabs value={tab} onValueChange={cambiarTab} className="gap-4">
          <div className="overflow-x-auto pb-1">
            <TabsList variant="line" className="w-max gap-4">
              <TabsTrigger
                value="acreditaciones"
                className="px-3 text-xs font-black uppercase tracking-wider"
              >
                Acreditaciones
              </TabsTrigger>
              <TabsTrigger
                value="accesos"
                className="px-3 text-xs font-black uppercase tracking-wider"
              >
                Registro de accesos
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="acreditaciones" className="mt-4">
            <PanelAcreditaciones />
          </TabsContent>

          <TabsContent value="accesos" className="mt-4">
            <PanelAccesos />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}

/** Tab 1 — the accreditations (A10) and their drilldown (A11). */
function PanelAcreditaciones() {
  const control = useAdminControlLista(
    PREFIJO_ACREDITACIONES,
    OTROS_ACREDITACIONES,
  );
  const detalle = useAdminDetalleUrl(PREFIJO_ACREDITACIONES);
  const catalogos = useAdminCatalogos();
  const consulta = useAdminAcreditaciones(control.estado);
  const consultaDetalle = useAdminAcreditacionDetalle(detalle.detalleId);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(
    () => adminOpcionesOrdering(ORDEN_ACREDITACIONES),
    [],
  );
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminAcreditacionListItem>[] = [
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
        <AdminEstadoBadge
          etiqueta={estadoAcreditacionLabel(item.estado)}
          tono={estadoAcreditacionTone(item.estado)}
        />
      ),
    },
    {
      clave: "acceso_fiesta",
      etiqueta: "Acceso fiesta",
      render: (item) => (
        <span className="text-xs font-bold text-slate-800">
          {item.acceso_fiesta ? "Sí" : "No"}
        </span>
      ),
    },
    {
      clave: "autorizacion",
      etiqueta: "Autorización",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={autorizacionFiestaLabel(item.autorizacion_fiesta)}
          tono={autorizacionFiestaTone(item.autorizacion_fiesta)}
        />
      ),
    },
    {
      clave: "habilitado",
      etiqueta: "Habilitado",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {item.habilitado === null ? "—" : item.habilitado ? "Sí" : "No"}
        </span>
      ),
    },
    {
      clave: "accesos",
      etiqueta: "Accesos permitidos",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {item.accesos_permitidos}
        </span>
      ),
    },
    {
      clave: "ultimo",
      etiqueta: "Último acceso",
      render: (item) => (
        <span className="text-slate-600">
          {item.ultimo_acceso ? formatearFecha(item.ultimo_acceso) : "—"}
        </span>
      ),
    },
  ];

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  return (
    <>
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
        orden={control.estado.ordering || ORDEN_POR_DEFECTO_ACREDITACIONES}
        opcionesOrden={opcionesOrden}
        onCambiarOrden={control.onCambiarOrden}
        controles={
          <>
            <AdminFiltroSelect
              etiqueta="Estado"
              valor={control.estado.filtros.estado ?? ""}
              opciones={(catalogo?.estados.acreditacion ?? []).map((valor) => ({
                valor,
                etiqueta: estadoAcreditacionLabel(valor),
              }))}
              onChange={(valor) => control.onFiltro("estado", valor)}
            />
            <AdminFiltroSelect
              etiqueta="Autorización"
              valor={control.estado.filtros.autorizacion_fiesta ?? ""}
              opciones={(catalogo?.estados.autorizacion_fiesta ?? []).map(
                (valor) => ({
                  valor,
                  etiqueta: autorizacionFiestaLabel(valor),
                }),
              )}
              onChange={(valor) =>
                control.onFiltro("autorizacion_fiesta", valor)
              }
            />
            <AdminFiltroSelect
              etiqueta="Acceso a la fiesta"
              valor={control.estado.filtros.acceso_fiesta ?? ""}
              opciones={[
                { valor: "true", etiqueta: "Con acceso" },
                { valor: "false", etiqueta: "Sin acceso" },
              ]}
              onChange={(valor) => control.onFiltro("acceso_fiesta", valor)}
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
                  {item.persona_nombre}
                </span>
                <span className="text-[11px] text-slate-500">
                  {item.persona_documento}
                </span>
              </div>
              <AdminEstadoBadge
                etiqueta={estadoAcreditacionLabel(item.estado)}
                tono={estadoAcreditacionTone(item.estado)}
              />
            </div>
            <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
              <span className="rounded-full bg-slate-100 px-2 py-1">
                Fiesta {item.acceso_fiesta ? "sí" : "no"}
              </span>
              <span className="rounded-full bg-slate-100 px-2 py-1">
                {autorizacionFiestaLabel(item.autorizacion_fiesta)}
              </span>
              <span className="rounded-full bg-slate-100 px-2 py-1">
                Accesos {item.accesos_permitidos}
              </span>
            </div>
          </div>
        )}
        onAbrir={(item) => {
          detalle.abrirDetalle(item.id);
        }}
        tituloVacio="Todavía no hay acreditaciones"
        descripcionVacia="No hay acreditaciones registradas en el evento activo."
      />

      <Sheet
        open={Boolean(detalle.detalleId)}
        onOpenChange={(abierto) => {
          if (!abierto) detalle.cerrarDetalle();
        }}
      >
        <SheetContent
          side="right"
          className="w-full overflow-y-auto sm:max-w-2xl"
        >
          <SheetHeader>
            <SheetTitle className="text-base font-black tracking-tight text-[#17214b]">
              Detalle de la acreditación
            </SheetTitle>
            <SheetDescription className="text-xs text-slate-500">
              Accesos registrados de esta acreditación. El código QR vivo nunca
              forma parte de esta respuesta.
            </SheetDescription>
          </SheetHeader>

          {consultaDetalle.isPending ? (
            <AdminListaSkeleton filas={4} />
          ) : consultaDetalle.error ? (
            <AdminListaError
              mensaje={consultaDetalle.error.message}
              onReintentar={() => {
                void consultaDetalle.refetch();
              }}
            />
          ) : (
            (() => {
              const acreditacion = consultaDetalle.data?.success
                ? consultaDetalle.data.data
                : null;

              if (!acreditacion) {
                return (
                  <AdminListaVacia
                    titulo="Acreditación no encontrada"
                    descripcion="La acreditación solicitada no existe o no pertenece al evento activo."
                  />
                );
              }

              return (
                <div className="space-y-5">
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      {
                        etiqueta: "Persona",
                        valor: acreditacion.persona_nombre,
                      },
                      {
                        etiqueta: "Documento",
                        valor: acreditacion.persona_documento,
                      },
                      {
                        etiqueta: "Estado",
                        valor: estadoAcreditacionLabel(acreditacion.estado),
                      },
                      {
                        etiqueta: "Autorización de fiesta",
                        valor: autorizacionFiestaLabel(
                          acreditacion.autorizacion_fiesta,
                        ),
                      },
                      {
                        etiqueta: "Acceso a la fiesta",
                        valor: acreditacion.acceso_fiesta ? "Sí" : "No",
                      },
                      {
                        etiqueta: "Acceso a box",
                        valor:
                          acreditacion.acceso_box === null
                            ? "—"
                            : acreditacion.acceso_box
                              ? "Sí"
                              : "No",
                      },
                      {
                        etiqueta: "Habilitado por el administrador",
                        valor:
                          acreditacion.habilitado === null
                            ? "—"
                            : acreditacion.habilitado
                              ? "Sí"
                              : "No",
                      },
                      {
                        etiqueta: "Accesos permitidos",
                        valor: String(acreditacion.accesos_permitidos),
                      },
                    ].map((bloque) => (
                      <div
                        key={bloque.etiqueta}
                        className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
                      >
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                          {bloque.etiqueta}
                        </p>
                        <p className="mt-1 text-sm font-bold text-slate-900">
                          {bloque.valor}
                        </p>
                      </div>
                    ))}
                  </div>

                  {acreditacion.observacion && (
                    <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
                      {acreditacion.observacion}
                    </p>
                  )}

                  <div>
                    <h3 className="mb-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#312e8e]">
                      Accesos ({acreditacion.accesos.length})
                    </h3>

                    {acreditacion.accesos.length === 0 ? (
                      <AdminListaVacia
                        titulo="Sin accesos"
                        descripcion="Esta acreditación todavía no registra ningún acceso."
                      />
                    ) : (
                      <div className="overflow-hidden rounded-2xl border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-b border-slate-100 bg-slate-50/70">
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Resultado
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Punto
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Operador
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Fecha
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {acreditacion.accesos.map((acceso) => (
                              <TableRow key={acceso.id}>
                                <TableCell className="py-2.5 text-xs">
                                  <AdminEstadoBadge
                                    etiqueta={resultadoAccesoLabel(
                                      acceso.resultado,
                                    )}
                                    tono={resultadoAccesoTone(acceso.resultado)}
                                  />
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {acceso.punto_acceso ?? "—"}
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {acceso.operador_nombre ?? "—"}
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {formatearFecha(acceso.fecha_hora)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

/** Tab 2 — the access log (A12). */
function PanelAccesos() {
  const control = useAdminControlLista(PREFIJO_ACCESOS, OTROS_ACCESOS);
  const catalogos = useAdminCatalogos();
  const consulta = useAdminAccesos(control.estado);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(() => adminOpcionesOrdering(ORDEN_ACCESOS), []);
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminAccesoListItem>[] = [
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
      clave: "resultado",
      etiqueta: "Resultado",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={resultadoAccesoLabel(item.resultado)}
          tono={resultadoAccesoTone(item.resultado)}
        />
      ),
    },
    {
      clave: "punto",
      etiqueta: "Punto de acceso",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {item.punto_acceso ?? "—"}
        </span>
      ),
    },
    {
      clave: "operador",
      etiqueta: "Operador",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {item.operador_nombre ?? "—"}
        </span>
      ),
    },
    {
      clave: "fecha",
      etiqueta: "Fecha y hora",
      render: (item) => (
        <span className="text-slate-600">
          {formatearFecha(item.fecha_hora)}
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
      orden={control.estado.ordering || ORDEN_POR_DEFECTO_ACCESOS}
      opcionesOrden={opcionesOrden}
      onCambiarOrden={control.onCambiarOrden}
      controles={
        <>
          <AdminFiltroSelect
            etiqueta="Resultado"
            valor={control.estado.filtros.resultado ?? ""}
            opciones={(catalogo?.estados.acceso ?? []).map((valor) => ({
              valor,
              etiqueta: resultadoAccesoLabel(valor),
            }))}
            onChange={(valor) => control.onFiltro("resultado", valor)}
          />
          <AdminFiltroSelect
            etiqueta="Punto de acceso"
            valor={control.estado.filtros.punto_acceso ?? ""}
            opciones={(catalogo?.puntos_acceso ?? []).map((valor) => ({
              valor,
              etiqueta: valor,
            }))}
            onChange={(valor) => control.onFiltro("punto_acceso", valor)}
          />
          <AdminFiltroRangoFechas
            etiqueta="Fechas"
            desde={control.estado.filtros.desde ?? ""}
            hasta={control.estado.filtros.hasta ?? ""}
            onChange={(desde, hasta) => control.onFiltros({ desde, hasta })}
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
                {item.persona_nombre}
              </span>
              <span className="text-[11px] text-slate-500">
                {item.persona_documento}
              </span>
            </div>
            <AdminEstadoBadge
              etiqueta={resultadoAccesoLabel(item.resultado)}
              tono={resultadoAccesoTone(item.resultado)}
            />
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {item.punto_acceso ?? "Sin punto"}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-1">
              {formatearFecha(item.fecha_hora)}
            </span>
          </div>
        </div>
      )}
      tituloVacio="Todavía no hay accesos"
      descripcionVacia="No hay accesos registrados en el evento activo."
    />
  );
}
