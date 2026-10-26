"use client";

import { ArrowLeft, CalendarClock, Trophy } from "lucide-react";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAdminInscripcionDetalle } from "../hooks/useAdminInscripciones";
import {
  estadoAsignacionLabel,
  estadoAsignacionTone,
  estadoCompraLabel,
  estadoCompraTone,
  estadoOrdenLabel,
  estadoOrdenTone,
  estadoPoolLabel,
  estadoPoolTone,
  medioAceptacionLabel,
  rolParticipanteLabel,
  tipoAceptacionLabel,
  tipoCompraLabel,
} from "../utils/admin.estado.utils";
import {
  estadoInscripcionLabel,
  estadoInscripcionTone,
  formatearFecha,
  formatearMonto,
} from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminEstadoBadge } from "./AdminEstadoBadge";
import {
  AdminListaError,
  AdminListaSkeleton,
  AdminListaVacia,
} from "./AdminListaEstados";

export interface AdminInscripcionDetalleProps {
  inscripcionId: string;
}

/**
 * AdminInscripcionDetalle — the drilldown of a registration (A4).
 *
 * The SIX documented blocks are six tabs: teams (with their roster),
 * participants, purchases, cup assignments, legal acceptances and the cup
 * balance. Every block is computed by the backend; this component only groups
 * and formats what it received.
 */
export function AdminInscripcionDetalle({
  inscripcionId,
}: AdminInscripcionDetalleProps) {
  const consulta = useAdminInscripcionDetalle(inscripcionId);

  if (consulta.error?.status === 403) {
    return <AdminAccessDenied message={consulta.error.message} />;
  }

  if (consulta.isPending) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
        <AdminListaSkeleton filas={8} />
      </div>
    );
  }

  if (consulta.error) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
        <AdminListaError
          mensaje={consulta.error.message}
          onReintentar={() => {
            void consulta.refetch();
          }}
        />
        <div className="mt-6 text-center">
          <Link
            href="/administracion/inscripciones"
            className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#312e8e]"
          >
            <ArrowLeft className="size-3.5" />
            Volver a las inscripciones
          </Link>
        </div>
      </div>
    );
  }

  const detalle = consulta.data?.success ? consulta.data.data : null;

  if (!detalle) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6">
        <AdminListaVacia
          titulo="Inscripción no encontrada"
          descripcion="La inscripción solicitada no existe o no pertenece al evento activo."
        />
        <div className="mt-6 text-center">
          <Link
            href="/administracion/inscripciones"
            className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#312e8e]"
          >
            <ArrowLeft className="size-3.5" />
            Volver a las inscripciones
          </Link>
        </div>
      </div>
    );
  }

  const saldo = detalle.saldo;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
      <Link
        href="/administracion/inscripciones"
        className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.25em] text-slate-500 transition-colors hover:text-[#312e8e]"
      >
        <ArrowLeft className="size-3.5" />
        Inscripciones
      </Link>

      <header className="mt-4 card-elevated p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <p className="text-eyebrow-brand">{detalle.evento_nombre}</p>
            <h1 className="text-xl font-black tracking-tight text-[#17214b] sm:text-2xl">
              {detalle.responsable_nombre}
            </h1>
            <p className="text-xs text-slate-500">
              {detalle.responsable_documento} · {detalle.paquete_nombre} ·{" "}
              {detalle.promocion_nombre}
            </p>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <AdminEstadoBadge
              etiqueta={estadoInscripcionLabel(detalle.estado)}
              tono={estadoInscripcionTone(detalle.estado)}
            />
            {detalle.delegado_nombre && (
              <span className="text-[11px] text-slate-600">
                Delegado: {detalle.delegado_nombre}
              </span>
            )}
            {detalle.fecha_limite_modificacion && (
              <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-600">
                <CalendarClock className="size-3.5" />
                Modificaciones hasta el{" "}
                {formatearFecha(detalle.fecha_limite_modificacion)}
              </span>
            )}
          </div>
        </div>

        {detalle.observacion && (
          <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
            {detalle.observacion}
          </p>
        )}
      </header>

      <Tabs defaultValue="equipos" className="mt-6 gap-4">
        <div className="overflow-x-auto pb-1">
          <TabsList variant="line" className="w-max gap-4">
            <TabsTrigger
              value="equipos"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Equipos ({detalle.equipos.length})
            </TabsTrigger>
            <TabsTrigger
              value="participantes"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Participantes ({detalle.participantes.length})
            </TabsTrigger>
            <TabsTrigger
              value="compras"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Compras ({detalle.compras.length})
            </TabsTrigger>
            <TabsTrigger
              value="asignaciones"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Asignaciones ({detalle.asignaciones.length})
            </TabsTrigger>
            <TabsTrigger
              value="aceptaciones"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Aceptaciones ({detalle.aceptaciones.length})
            </TabsTrigger>
            <TabsTrigger
              value="saldo"
              className="px-3 text-xs font-black uppercase tracking-wider"
            >
              Saldo
            </TabsTrigger>
          </TabsList>
        </div>

        {/* 1 — Teams (with their roster) */}
        <TabsContent value="equipos" className="mt-4">
          {detalle.equipos.length === 0 ? (
            <AdminListaVacia
              titulo="Sin equipos"
              descripcion="Esta inscripción todavía no tiene equipos registrados."
            />
          ) : (
            <div className="flex flex-col gap-3">
              {detalle.equipos.map((equipo) => (
                <article key={equipo.id} className="card-elevated p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Trophy className="size-4 text-[#312e8e]" />
                      <div>
                        <h3 className="text-sm font-black text-slate-900">
                          {equipo.nombre}
                        </h3>
                        <p className="text-[11px] text-slate-500">
                          {equipo.disciplina_nombre} ·{" "}
                          {equipo.categoria_nombre ?? "—"} ·{" "}
                          {equipo.inscripcion_ref}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-black uppercase tracking-wider text-slate-700">
                        Plantilla {equipo.jugadores_registrados}/
                        {equipo.minimo_deportivo}
                      </span>
                      <AdminEstadoBadge
                        etiqueta={equipo.estado_roster}
                        tono={
                          equipo.estado_roster === "COMPLETO"
                            ? "emerald"
                            : "amber"
                        }
                      />
                    </div>
                  </div>

                  {equipo.participaciones.length > 0 && (
                    <>
                      <div className="mt-3 hidden overflow-hidden rounded-2xl border border-slate-100 lg:block">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-b border-slate-100 bg-slate-50/70">
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Persona
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Rol
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Talla
                              </TableHead>
                              <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                                Estado
                              </TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {equipo.participaciones.map((participacion) => (
                              <TableRow key={participacion.id}>
                                <TableCell className="py-2.5 text-xs">
                                  <span className="font-bold text-slate-900">
                                    {participacion.persona_nombre}
                                  </span>
                                  <span className="block text-[11px] text-slate-500">
                                    {participacion.persona_documento}
                                  </span>
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {rolParticipanteLabel(participacion.rol)}
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {participacion.talla_camiseta}
                                </TableCell>
                                <TableCell className="py-2.5 text-xs">
                                  {participacion.estado}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>

                      <ul className="mt-3 flex flex-col gap-2 lg:hidden">
                        {equipo.participaciones.map((participacion) => (
                          <li
                            key={participacion.id}
                            className="rounded-xl border border-slate-100 bg-slate-50/60 p-3"
                          >
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div className="flex flex-col">
                                <span className="text-xs font-black text-slate-900">
                                  {participacion.persona_nombre}
                                </span>
                                <span className="text-[11px] text-slate-500">
                                  {participacion.persona_documento}
                                </span>
                              </div>
                              <span className="rounded-full bg-white px-2 py-1 text-[10px] font-black uppercase tracking-wider text-slate-600">
                                {rolParticipanteLabel(participacion.rol)}
                              </span>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-600">
                              <span className="rounded-full bg-white px-2 py-1">
                                Talla: {participacion.talla_camiseta}
                              </span>
                              <span className="rounded-full bg-white px-2 py-1">
                                Estado: {participacion.estado}
                              </span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </article>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 2 — Participants */}
        <TabsContent value="participantes" className="mt-4">
          {detalle.participantes.length === 0 ? (
            <AdminListaVacia
              titulo="Sin participantes"
              descripcion="Esta inscripción todavía no tiene personas registradas."
            />
          ) : (
            <>
              <div className="card-elevated hidden overflow-hidden lg:block">
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-slate-100 bg-slate-50/70">
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Persona
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Estado pool
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Cupo activo
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Disciplinas
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detalle.participantes.map((participante) => (
                      <TableRow key={participante.inscripcion_persona_id}>
                        <TableCell className="py-3 text-xs">
                          <span className="font-bold text-slate-900">
                            {participante.persona_nombre}
                          </span>
                          <span className="block text-[11px] text-slate-500">
                            {participante.persona_documento}
                          </span>
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          <AdminEstadoBadge
                            etiqueta={estadoPoolLabel(participante.estado_pool)}
                            tono={estadoPoolTone(participante.estado_pool)}
                          />
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {participante.tiene_cupo_activo ? "Sí" : "No"}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {participante.disciplinas.length > 0
                            ? participante.disciplinas.join(", ")
                            : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <ul className="flex flex-col gap-3 lg:hidden">
                {detalle.participantes.map((participante) => (
                  <li
                    key={participante.inscripcion_persona_id}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-black text-slate-900">
                          {participante.persona_nombre}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {participante.persona_documento}
                        </span>
                      </div>
                      <AdminEstadoBadge
                        etiqueta={estadoPoolLabel(participante.estado_pool)}
                        tono={estadoPoolTone(participante.estado_pool)}
                      />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-600">
                      <span className="rounded-full bg-slate-100 px-2 py-1">
                        Cupo activo:{" "}
                        {participante.tiene_cupo_activo ? "Sí" : "No"}
                      </span>
                      <span className="rounded-full bg-slate-100 px-2 py-1">
                        Disciplinas:{" "}
                        {participante.disciplinas.length > 0
                          ? participante.disciplinas.join(", ")
                          : "—"}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </TabsContent>

        {/* 3 — Purchases */}
        <TabsContent value="compras" className="mt-4">
          {detalle.compras.length === 0 ? (
            <AdminListaVacia
              titulo="Sin compras"
              descripcion="Esta inscripción todavía no tiene compras registradas."
            />
          ) : (
            <>
              <div className="card-elevated hidden overflow-hidden lg:block">
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-slate-100 bg-slate-50/70">
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Tipo
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Cantidad
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Total
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Compra
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Orden
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detalle.compras.map((compra) => (
                      <TableRow
                        key={`${compra.compra_id}-${compra.created_at}`}
                      >
                        <TableCell className="py-3 text-xs font-bold text-slate-900">
                          {tipoCompraLabel(compra.tipo)}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {compra.cantidad}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {formatearMonto(compra.total)}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          <AdminEstadoBadge
                            etiqueta={estadoCompraLabel(compra.estado_compra)}
                            tono={estadoCompraTone(compra.estado_compra)}
                          />
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {compra.estado_orden ? (
                            <AdminEstadoBadge
                              etiqueta={estadoOrdenLabel(compra.estado_orden)}
                              tono={estadoOrdenTone(compra.estado_orden)}
                            />
                          ) : (
                            "—"
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <ul className="flex flex-col gap-3 lg:hidden">
                {detalle.compras.map((compra) => (
                  <li
                    key={`${compra.compra_id}-${compra.created_at}`}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <span className="text-sm font-black text-slate-900">
                        {tipoCompraLabel(compra.tipo)}
                      </span>
                      <span className="text-sm font-black text-slate-900">
                        {formatearMonto(compra.total)}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <AdminEstadoBadge
                        etiqueta={estadoCompraLabel(compra.estado_compra)}
                        tono={estadoCompraTone(compra.estado_compra)}
                      />
                      {compra.estado_orden ? (
                        <AdminEstadoBadge
                          etiqueta={estadoOrdenLabel(compra.estado_orden)}
                          tono={estadoOrdenTone(compra.estado_orden)}
                        />
                      ) : null}
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-600">
                        {compra.cantidad} cupo(s)
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </TabsContent>

        {/* 4 — Cup assignments */}
        <TabsContent value="asignaciones" className="mt-4">
          {detalle.asignaciones.length === 0 ? (
            <AdminListaVacia
              titulo="Sin asignaciones"
              descripcion="Todavía no se asignó ningún cupo pagado a una persona."
            />
          ) : (
            <>
              <div className="card-elevated hidden overflow-hidden lg:block">
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-slate-100 bg-slate-50/70">
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Persona
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Estado
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Motivo
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Liberada
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detalle.asignaciones.map((asignacion) => (
                      <TableRow key={asignacion.id}>
                        <TableCell className="py-3 text-xs font-bold text-slate-900">
                          {asignacion.persona_nombre}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          <AdminEstadoBadge
                            etiqueta={estadoAsignacionLabel(asignacion.estado)}
                            tono={estadoAsignacionTone(asignacion.estado)}
                          />
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {asignacion.motivo ?? "—"}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {asignacion.liberada_en
                            ? formatearFecha(asignacion.liberada_en)
                            : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <ul className="flex flex-col gap-3 lg:hidden">
                {detalle.asignaciones.map((asignacion) => (
                  <li
                    key={asignacion.id}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <span className="text-sm font-black text-slate-900">
                        {asignacion.persona_nombre}
                      </span>
                      <AdminEstadoBadge
                        etiqueta={estadoAsignacionLabel(asignacion.estado)}
                        tono={estadoAsignacionTone(asignacion.estado)}
                      />
                    </div>
                    <p className="mt-2 text-xs text-slate-600">
                      {asignacion.motivo ?? "—"}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Liberada:{" "}
                      {asignacion.liberada_en
                        ? formatearFecha(asignacion.liberada_en)
                        : "—"}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </TabsContent>

        {/* 5 — Legal acceptances */}
        <TabsContent value="aceptaciones" className="mt-4">
          {detalle.aceptaciones.length === 0 ? (
            <AdminListaVacia
              titulo="Sin aceptaciones"
              descripcion="Nadie de esta inscripción aceptó todavía las bases, la aptitud física o el uso de imagen."
            />
          ) : (
            <>
              <div className="card-elevated hidden overflow-hidden lg:block">
                <Table>
                  <TableHeader>
                    <TableRow className="border-b border-slate-100 bg-slate-50/70">
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Aceptación
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Versión
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Medio
                      </TableHead>
                      <TableHead className="text-[10px] font-black uppercase tracking-wider text-slate-500">
                        Aceptado
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detalle.aceptaciones.map((aceptacion) => (
                      <TableRow
                        key={`${aceptacion.persona_id}-${aceptacion.tipo_aceptacion}`}
                      >
                        <TableCell className="py-3 text-xs font-bold text-slate-900">
                          {tipoAceptacionLabel(aceptacion.tipo_aceptacion)}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {aceptacion.documento_version}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {medioAceptacionLabel(aceptacion.medio)}
                        </TableCell>
                        <TableCell className="py-3 text-xs">
                          {formatearFecha(aceptacion.aceptado_en)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <ul className="flex flex-col gap-3 lg:hidden">
                {detalle.aceptaciones.map((aceptacion) => (
                  <li
                    key={`${aceptacion.persona_id}-${aceptacion.tipo_aceptacion}`}
                    className="rounded-2xl border border-slate-200 bg-white p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <span className="text-sm font-black text-slate-900">
                        {tipoAceptacionLabel(aceptacion.tipo_aceptacion)}
                      </span>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-600">
                        v{aceptacion.documento_version}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-600">
                      {medioAceptacionLabel(aceptacion.medio)}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Aceptado: {formatearFecha(aceptacion.aceptado_en)}
                    </p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </TabsContent>

        {/* 6 — Cup balance */}
        <TabsContent value="saldo" className="mt-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { etiqueta: "Cupos contratados", valor: saldo.contratados },
              { etiqueta: "Cupos pagados", valor: saldo.pagados },
              {
                etiqueta: "Cupos asignados (pagados)",
                valor: saldo.asignados_pagados,
              },
              {
                etiqueta: "Cupos disponibles (pagados)",
                valor: saldo.disponibles_pagados,
              },
            ].map((bloque) => (
              <div key={bloque.etiqueta} className="card-elevated p-5">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                  {bloque.etiqueta}
                </p>
                <p className="mt-2 text-2xl font-black tracking-tight text-[#17214b]">
                  {bloque.valor}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-4 text-xs leading-relaxed text-slate-500">
            El saldo lo calcula el servidor con los cupos pagados y las
            asignaciones vigentes. La vista nunca recalcula ninguno de esos
            números.
          </p>
        </TabsContent>
      </Tabs>
    </div>
  );
}
