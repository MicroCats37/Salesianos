"use client";

import { UserCog } from "lucide-react";
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
import { useAdminControlLista } from "../hooks/useAdminControlLista";
import { useAdminDetalleUrl } from "../hooks/useAdminListaUrl";
import {
  useAdminUsuarioDetalle,
  useAdminUsuarios,
} from "../hooks/useAdminUsuarios";
import type { AdminUsuarioListItem } from "../schemas";
import { adminOpcionesOrdering } from "../utils/admin.lista.utils";
import {
  ORDEN_POR_DEFECTO_USUARIOS,
  ORDEN_USUARIOS,
} from "../utils/admin.orden.utils";
import {
  estadoInscripcionLabel,
  estadoInscripcionTone,
  formatearFecha,
} from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import { AdminFiltroSelect } from "./AdminFiltroSelect";
import {
  AdminListaError,
  AdminListaSkeleton,
  AdminListaVacia,
} from "./AdminListaEstados";
import { type AdminColumna, AdminListaOperativa } from "./AdminListaOperativa";
import { AdminPageHeader } from "./AdminPageHeader";

/**
 * AdminUsuariosLista — the accounts table (A13) and its drilldown (A14).
 *
 * The surface is READ-ONLY: it never manages a password, it never exposes a
 * hash or a token, and it never surfaces the break-glass tier. The `es_admin`
 * flag is the one the backend computes with `is_staff OR is_superuser`.
 */
export function AdminUsuariosLista() {
  const control = useAdminControlLista();
  const detalle = useAdminDetalleUrl();
  const consulta = useAdminUsuarios(control.estado);
  const consultaDetalle = useAdminUsuarioDetalle(detalle.detalleId);

  const datos = consulta.data?.success ? consulta.data.data : null;
  const items = datos?.items ?? [];

  const opcionesOrden = useMemo(
    () => adminOpcionesOrdering(ORDEN_USUARIOS),
    [],
  );

  const columnas: AdminColumna<AdminUsuarioListItem>[] = [
    {
      clave: "usuario",
      etiqueta: "Usuario",
      render: (item) => (
        <span className="font-black text-slate-900">{item.username}</span>
      ),
    },
    {
      clave: "nombre",
      etiqueta: "Nombre",
      render: (item) => (
        <span className="text-xs font-bold text-slate-800">
          {`${item.nombres} ${item.apellidos}`.trim()}
        </span>
      ),
    },
    {
      clave: "email",
      etiqueta: "Correo",
      render: (item) => (
        <span className="text-xs text-slate-600">{item.email ?? "—"}</span>
      ),
    },
    {
      clave: "documento",
      etiqueta: "Documento",
      render: (item) => (
        <span className="text-xs text-slate-600">{item.persona_documento}</span>
      ),
    },
    {
      clave: "rol",
      etiqueta: "Rol",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={item.es_admin ? "Administrador" : "Participante"}
          tono={item.es_admin ? "brand" : "slate"}
        />
      ),
    },
    {
      clave: "estado",
      etiqueta: "Estado",
      render: (item) => (
        <AdminEstadoBadge
          etiqueta={item.is_active ? "Activo" : "Inactivo"}
          tono={item.is_active ? "emerald" : "slate"}
        />
      ),
    },
    {
      clave: "ultimo",
      etiqueta: "Último acceso",
      render: (item) => (
        <span className="text-slate-600">
          {item.last_login ? formatearFecha(item.last_login) : "—"}
        </span>
      ),
    },
    {
      clave: "creado",
      etiqueta: "Creado",
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
        title="Usuarios"
        description="Cuentas registradas con su identidad civil y su rol en el evento. Esta sección es de solo lectura: no gestiona contraseñas ni expone credenciales."
        icon={UserCog}
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
          orden={control.estado.ordering || ORDEN_POR_DEFECTO_USUARIOS}
          opcionesOrden={opcionesOrden}
          onCambiarOrden={control.onCambiarOrden}
          controles={
            <>
              <AdminFiltroSelect
                etiqueta="Estado"
                valor={control.estado.filtros.estado ?? ""}
                opciones={[
                  { valor: "activo", etiqueta: "Activo" },
                  { valor: "inactivo", etiqueta: "Inactivo" },
                ]}
                onChange={(valor) => control.onFiltro("estado", valor)}
              />
              <AdminFiltroSelect
                etiqueta="Rol"
                valor={control.estado.filtros.es_admin ?? ""}
                opciones={[
                  { valor: "true", etiqueta: "Administrador" },
                  { valor: "false", etiqueta: "Participante" },
                ]}
                onChange={(valor) => control.onFiltro("es_admin", valor)}
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
                    {item.username}
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {`${item.nombres} ${item.apellidos}`.trim()}
                  </span>
                </div>
                <AdminEstadoBadge
                  etiqueta={item.es_admin ? "Administrador" : "Participante"}
                  tono={item.es_admin ? "brand" : "slate"}
                />
              </div>
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-600">
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  {item.email ?? "Sin correo"}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1">
                  {item.is_active ? "Activo" : "Inactivo"}
                </span>
              </div>
            </div>
          )}
          onAbrir={(item) => {
            detalle.abrirDetalle(item.id);
          }}
          tituloVacio="Todavía no hay usuarios"
          descripcionVacia="No hay cuentas registradas en el sistema."
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
                Detalle de la cuenta
              </SheetTitle>
              <SheetDescription className="text-xs text-slate-500">
                Inscripciones que esta cuenta posee dentro del evento activo. La
                contraseña nunca forma parte de esta respuesta.
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
                const usuario = consultaDetalle.data?.success
                  ? consultaDetalle.data.data
                  : null;

                if (!usuario) {
                  return (
                    <AdminListaVacia
                      titulo="Cuenta no encontrada"
                      descripcion="La cuenta solicitada no existe."
                    />
                  );
                }

                return (
                  <div className="space-y-5">
                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        { etiqueta: "Usuario", valor: usuario.username },
                        {
                          etiqueta: "Nombre",
                          valor:
                            `${usuario.nombres} ${usuario.apellidos}`.trim(),
                        },
                        { etiqueta: "Correo", valor: usuario.email ?? "—" },
                        {
                          etiqueta: "Documento",
                          valor: usuario.persona_documento,
                        },
                        {
                          etiqueta: "Rol",
                          valor: usuario.es_admin
                            ? "Administrador"
                            : "Participante",
                        },
                        {
                          etiqueta: "Estado",
                          valor: usuario.is_active ? "Activo" : "Inactivo",
                        },
                        {
                          etiqueta: "Último acceso",
                          valor: usuario.last_login
                            ? formatearFecha(usuario.last_login)
                            : "—",
                        },
                        {
                          etiqueta: "Creado",
                          valor: formatearFecha(usuario.created_at),
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
                        Inscripciones del evento ({usuario.personas.length})
                      </h3>

                      {usuario.personas.length === 0 ? (
                        <AdminListaVacia
                          titulo="Sin inscripciones"
                          descripcion="Esta cuenta no posee inscripciones en el evento activo."
                        />
                      ) : (
                        <div className="overflow-hidden rounded-2xl border border-slate-200">
                          <Table>
                            <TableHeader>
                              <TableRow className="border-b border-slate-100 bg-slate-50/70">
                                <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                  Estado
                                </TableHead>
                                <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                  Creada
                                </TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {usuario.personas.map((inscripcion) => (
                                <TableRow key={inscripcion.inscripcion_id}>
                                  <TableCell className="py-2.5 text-xs">
                                    <AdminEstadoBadge
                                      etiqueta={estadoInscripcionLabel(
                                        inscripcion.estado,
                                      )}
                                      tono={estadoInscripcionTone(
                                        inscripcion.estado,
                                      )}
                                    />
                                  </TableCell>
                                  <TableCell className="py-2.5 text-xs">
                                    {formatearFecha(inscripcion.created_at)}
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
      </div>
    </>
  );
}
