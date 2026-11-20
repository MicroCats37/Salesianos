import { AlertTriangle, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminCifras,
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";
import type { EstadoResumenAdmin } from "../types/resumen-admin.types";

/**
 * ADM-01: the operational summary of the edition.
 *
 * The summary is a reading surface: it never writes. Its content is the
 * edition in force, the figures the backend published and the ISSUES that
 * require attention, each one with the authorized action that resolves it.
 *
 * ## What the browser does NOT do
 *
 * - It does NOT recalculate a figure: the number is the one the server sent.
 * - It does NOT decide which view an issue leads to: the `href` is a fact of
 *   the backend, already FILTERED.
 * - It does NOT invent an issue: the list is the one the server published.
 */
export function AdminResumenView({ estado }: { estado: EstadoResumenAdmin }) {
  const listo = estado.estado === "listo";

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-01"
        title="Estado operativo de la edición"
        description="El estado de la edición activa en un vistazo: inscripciones, pagos, cupos, pases, equipos y participantes, con lo que requiere atención en primer lugar."
        actions={
          <Button asChild className="min-h-11">
            <Link href={RUTAS.administracion.inscripciones}>
              Ir a inscripciones
            </Link>
          </Button>
        }
      />

      <AdminNotice title="Superficie de solo lectura">
        El resumen no escribe nada: publica el estado que calcula el backend.
        Ninguna cifra de esta pantalla se recalcula en el navegador.
      </AdminNotice>

      <AdminPanel
        title="Edición activa"
        description="Nombre de la edición y estado en el que se resuelve el resumen."
      >
        {listo ? (
          <AdminDataTable
            caption="La edición en la que se resuelve el resumen"
            columns={[
              { key: "edicion", label: "Edición" },
              { key: "estado", label: "Estado" },
            ]}
            filas={[
              {
                cells: {
                  edicion: (
                    <span className="font-medium text-foreground">
                      {estado.datos.edicion_nombre}
                    </span>
                  ),
                  estado: (
                    <span className="text-muted-foreground">
                      {estado.datos.edicion_estado}
                    </span>
                  ),
                },
              },
            ]}
          />
        ) : (
          <AdminEmptyState
            icon={LayoutDashboard}
            title={tituloDelEstado(estado.estado)}
            description={descripcionDelEstado(estado)}
          />
        )}
      </AdminPanel>

      <AdminPanel
        title="Cifras del resumen"
        description="Lo que el backend calcula para la edición en curso."
      >
        {listo ? (
          estado.datos.metricas.length > 0 ? (
            <AdminCifras
              etiqueta="Cifras del resumen operativo de la edición"
              cifras={estado.datos.metricas.map((metrica) => ({
                codigo: metrica.codigo,
                etiqueta: metrica.etiqueta,
                descripcion: metrica.descripcion,
                valor: metrica.valor,
              }))}
            />
          ) : (
            <AdminEmptyState
              icon={LayoutDashboard}
              title="Todavía no hay cifras"
              description="La edición en curso no tiene registros que resumir."
            />
          )
        ) : null}
      </AdminPanel>

      <AdminPanel
        title="Lo que requiere atención"
        description="Cada incidencia lleva la acción autorizada que la resuelve."
      >
        {listo ? (
          <AdminDataTable
            caption="Incidencias del resumen operativo y su acción"
            columns={[
              { key: "incidencia", label: "Incidencia" },
              { key: "que_pasa", label: "Qué pasa" },
              { key: "registros", label: "Registros", numerico: true },
              { key: "accion", label: "Acción" },
            ]}
            filas={estado.datos.incidencias.map((incidencia) => ({
              cells: {
                incidencia: (
                  <span className="font-medium text-foreground">
                    {incidencia.etiqueta}
                  </span>
                ),
                que_pasa: (
                  <span className="whitespace-normal text-muted-foreground">
                    {incidencia.descripcion}
                  </span>
                ),
                registros: (
                  <span className="tabular-nums">{incidencia.cantidad}</span>
                ),
                accion: (
                  <Link
                    href={incidencia.accion.href}
                    className="text-primary underline underline-offset-4"
                  >
                    {incidencia.accion.etiqueta}
                  </Link>
                ),
              },
            }))}
            vacio={
              <AdminEmptyState
                icon={AlertTriangle}
                title="No hay incidencias abiertas"
                description="La edición en curso no tiene nada que requiere atención."
              />
            }
          />
        ) : null}
      </AdminPanel>
    </div>
  );
}

function tituloDelEstado(estado: string): string {
  if (estado === "cargando") return "Cargando el resumen";
  if (estado === "sin-permiso") {
    return "No tienes autorización para ver el resumen";
  }
  if (estado === "error") return "No se pudo leer el resumen";
  return "Todavía no hay un resumen enlazado";
}

function descripcionDelEstado(estado: {
  estado: string;
  mensaje?: string;
}): string {
  if (estado.estado === "sin-datos") {
    return "El resumen se apoya en la edición que resuelve el backend. Cuando la ruta esté registrada, aquí se verán las cifras y las incidencias de la edición.";
  }

  return estado.mensaje ?? "El backend no pudo responder.";
}
