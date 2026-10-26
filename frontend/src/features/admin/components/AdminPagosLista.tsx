"use client";

import { CreditCard } from "lucide-react";
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
import { useAdminCatalogos } from "../hooks/useAdminCatalogos";
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import { useAdminDetalleUrl } from "../hooks/useAdminListaUrl";
import { useAdminPagoDetalle, useAdminPagos } from "../hooks/useAdminPagos";
import type { AdminPagoListItem } from "../schemas";
import {
  estadoCompraLabel,
  estadoCompraTone,
  estadoOrdenLabel,
  estadoOrdenTone,
  estadoTransaccionLabel,
  estadoTransaccionTone,
  tipoCompraLabel,
} from "../utils/admin.estado.utils";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_PAGOS,
  ORDEN_POR_DEFECTO_PAGOS,
} from "../utils/admin.orden.utils";
import { formatearFecha, formatearMonto } from "../utils/admin.resumen.utils";
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
 * AdminPagosLista — the payments table (A5) and the drilldown of one order
 * (A6).
 *
 * The wrapper of the backend carries EXPLICIT fields only: the payment
 * metadata, the session token, the provider message and the transaction id
 * are not modelled, so they can never be rendered.
 */
export function AdminPagosLista() {
  const control = useAdminControlLista();
  const detalle = useAdminDetalleUrl();
  const catalogos = useAdminCatalogos();
  const consulta = useAdminPagos(control.estado);
  const consultaDetalle = useAdminPagoDetalle(detalle.detalleId);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(() => adminOpcionesOrdering(ORDEN_PAGOS), []);
  const catalogo = catalogos.data?.success ? catalogos.data.data : null;

  const columnas: AdminColumna<AdminPagoListItem>[] = [
    {
      clave: "orden",
      etiqueta: "N° orden",
      render: (item) => (
        <span className="font-black text-slate-900">
          {item.numero_orden ?? "—"}
        </span>
      ),
    },
    {
      clave: "responsable",
      etiqueta: "Responsable",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {item.responsable_nombre}
        </span>
      ),
    },
    {
      clave: "tipo",
      etiqueta: "Tipo",
      render: (item) => (
        <span className="text-xs text-slate-600">
          {tipoCompraLabel(item.tipo)}
        </span>
      ),
    },
    {
      clave: "cantidad",
      etiqueta: "Cantidad",
      render: (item) => <span className="font-bold">{item.cantidad}</span>,
    },
    {
      clave: "total",
      etiqueta: "Total",
      render: (item) => (
        <span className="font-bold text-slate-800">
          {formatearMonto(item.total)}
        </span>
      ),
    },
    {
      clave: "estado_compra",
      etiqueta: "Estado compra",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={estadoCompraLabel(item.estado_compra)}
          tono={estadoCompraTone(item.estado_compra)}
        />
      ),
    },
    {
      clave: "estado_orden",
      etiqueta: "Estado orden",
      render: (item) =>
        item.estado_orden ? (
          <AdminEstadoBadge
            etiqueta={estadoOrdenLabel(item.estado_orden)}
            tono={estadoOrdenTone(item.estado_orden)}
          />
        ) : (
          <span className="text-xs text-slate-400">Sin orden</span>
        ),
    },
    {
      clave: "pagada",
      etiqueta: "Pagada el",
      render: (item) => (
        <span className="text-slate-600">
          {item.pagada_en ? formatearFecha(item.pagada_en) : "—"}
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
        title="Pagos"
        description="Compras y órdenes de pago del evento activo con su estado comercial y su estado de orden. Los montos provienen del snapshot congelado de la compra."
        icon={CreditCard}
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
          orden={control.estado.ordering || ORDEN_POR_DEFECTO_PAGOS}
          opcionesOrden={opcionesOrden}
          onCambiarOrden={control.onCambiarOrden}
          controles={
            <>
              <AdminFiltroSelect
                etiqueta="Estado de la compra"
                valor={control.estado.filtros.estado_compra ?? ""}
                opciones={(catalogo?.estados.compra ?? []).map((valor) => ({
                  valor,
                  etiqueta: estadoCompraLabel(valor),
                }))}
                onChange={(valor) => control.onFiltro("estado_compra", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Estado de la orden"
                valor={control.estado.filtros.estado_orden ?? ""}
                opciones={(catalogo?.estados.orden_pago ?? []).map((valor) => ({
                  valor,
                  etiqueta: estadoOrdenLabel(valor),
                }))}
                onChange={(valor) => control.onFiltro("estado_orden", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Tipo"
                valor={control.estado.filtros.tipo ?? ""}
                opciones={[
                  { valor: "INICIAL", etiqueta: "Inicial" },
                  { valor: "AMPLIACION", etiqueta: "Ampliación" },
                ]}
                onChange={(valor) => control.onFiltro("tipo", valor)}
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
          claveItem={(item) => `${item.compra_id}-${item.created_at}`}
          renderTarjeta={(item) => (
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col">
                  <span className="text-sm font-black text-slate-900">
                    {item.numero_orden ?? item.compra_id}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {item.responsable_nombre} · {tipoCompraLabel(item.tipo)}
                  </span>
                </div>
                <AdminEstadoBadge
                  etiqueta={estadoCompraLabel(item.estado_compra)}
                  tono={estadoCompraTone(item.estado_compra)}
                />
              </div>
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  {item.cantidad} cupo(s)
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  {formatearMonto(item.total)}
                </span>
                {item.estado_orden && (
                  <span className="rounded-full bg-slate-100 px-2 py-1">
                    Orden: {estadoOrdenLabel(item.estado_orden)}
                  </span>
                )}
              </div>
            </div>
          )}
          onAbrir={(item) => {
            if (item.orden_pago_id) {
              detalle.abrirDetalle(item.orden_pago_id);
            }
          }}
          tituloVacio="Todavía no hay pagos"
          descripcionVacia="No hay compras ni órdenes de pago registradas en el evento activo."
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
                Detalle de la orden de pago
              </SheetTitle>
              <SheetDescription className="text-xs text-slate-500">
                Intentos de pago registrados. El backend expone únicamente los
                campos explícitos y nunca los metadatos del proveedor.
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
                const pago = consultaDetalle.data?.success
                  ? consultaDetalle.data.data
                  : null;

                if (!pago) {
                  return (
                    <AdminListaVacia
                      titulo="Orden no encontrada"
                      descripcion="La orden solicitada no existe o no pertenece al evento activo."
                    />
                  );
                }

                return (
                  <div className="space-y-5">
                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        {
                          etiqueta: "N° orden",
                          valor: pago.numero_orden ?? "—",
                        },
                        {
                          etiqueta: "Responsable",
                          valor: pago.responsable_nombre,
                        },
                        { etiqueta: "Tipo", valor: tipoCompraLabel(pago.tipo) },
                        {
                          etiqueta: "Estado de la compra",
                          valor: estadoCompraLabel(pago.estado_compra),
                        },
                        {
                          etiqueta: "Estado de la orden",
                          valor: pago.estado_orden
                            ? estadoOrdenLabel(pago.estado_orden)
                            : "—",
                        },
                        {
                          etiqueta: "Total",
                          valor: formatearMonto(pago.total),
                        },
                        {
                          etiqueta: "Pagada el",
                          valor: pago.pagada_en
                            ? formatearFecha(pago.pagada_en)
                            : "—",
                        },
                        {
                          etiqueta: "Creada",
                          valor: formatearFecha(pago.created_at),
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

                    <div>
                      <h3 className="mb-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#312e8e]">
                        Intentos de pago ({pago.transacciones.length})
                      </h3>

                      {pago.transacciones.length === 0 ? (
                        <AdminListaVacia
                          titulo="Sin intentos"
                          descripcion="Esta orden todavía no registra intentos de pago."
                        />
                      ) : (
                        <>
                          <div className="hidden overflow-hidden rounded-2xl border border-slate-200 lg:block">
                            <Table>
                              <TableHeader>
                                <TableRow className="border-b border-slate-100 bg-slate-50/70">
                                  <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                    Estado
                                  </TableHead>
                                  <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                    Monto
                                  </TableHead>
                                  <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                    Método
                                  </TableHead>
                                  <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                    Código
                                  </TableHead>
                                  <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                    Fecha
                                  </TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {pago.transacciones.map((transaccion) => (
                                  <TableRow key={transaccion.id}>
                                    <TableCell className="py-2.5 text-xs">
                                      <AdminEstadoBadge
                                        etiqueta={estadoTransaccionLabel(
                                          transaccion.status,
                                        )}
                                        tono={estadoTransaccionTone(
                                          transaccion.status,
                                        )}
                                      />
                                    </TableCell>
                                    <TableCell className="py-2.5 text-xs font-bold">
                                      {formatearMonto(transaccion.amount)}
                                    </TableCell>
                                    <TableCell className="py-2.5 text-xs">
                                      {transaccion.metodo_pago ?? "—"}
                                    </TableCell>
                                    <TableCell className="py-2.5 text-xs">
                                      {transaccion.response_code ?? "—"}
                                    </TableCell>
                                    <TableCell className="py-2.5 text-xs">
                                      {formatearFecha(transaccion.created_at)}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </div>

                          <ul className="flex flex-col gap-2 lg:hidden">
                            {pago.transacciones.map((transaccion) => (
                              <li
                                key={transaccion.id}
                                className="rounded-2xl border border-slate-200 p-3"
                              >
                                <div className="flex flex-wrap items-start justify-between gap-2">
                                  <AdminEstadoBadge
                                    etiqueta={estadoTransaccionLabel(
                                      transaccion.status,
                                    )}
                                    tono={estadoTransaccionTone(
                                      transaccion.status,
                                    )}
                                  />
                                  <span className="text-xs font-black text-slate-900">
                                    {formatearMonto(transaccion.amount)}
                                  </span>
                                </div>
                                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600">
                                  <span className="rounded-full bg-slate-100 px-2 py-1">
                                    Método: {transaccion.metodo_pago ?? "—"}
                                  </span>
                                  <span className="rounded-full bg-slate-100 px-2 py-1">
                                    Código: {transaccion.response_code ?? "—"}
                                  </span>
                                  <span className="rounded-full bg-slate-100 px-2 py-1">
                                    {formatearFecha(transaccion.created_at)}
                                  </span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </>
                      )}
                    </div>
                  </div>
                );
              })()
            )}
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
