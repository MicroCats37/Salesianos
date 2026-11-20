import { Activity, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  AdminDataTable,
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { RUTAS } from "@/lib/routes";

/**
 * The blocks the summary publishes.
 *
 * They are NOT figures: they are the questions the operator asks of the
 * edition, and every one of them has a section where the answer can be
 * worked on. Listing them here is the honest content of the route while the
 * metrics service is not connected.
 */
const BLOQUES = [
  {
    bloque: "Inscripciones",
    pregunta: "Cuántas hay, en qué estado y cuántas se crearon esta semana.",
    href: RUTAS.administracion.inscripciones,
  },
  {
    bloque: "Pagos",
    pregunta:
      "Cuántas compras están pagadas, cuántas pendientes y qué monto falta.",
    href: RUTAS.administracion.pagos,
  },
  {
    bloque: "Cupos",
    pregunta: "Cuántos se contrataron, cuántos se pagaron y cuántos hay libres.",
    href: RUTAS.administracion.inscripciones,
  },
  {
    bloque: "Pases",
    pregunta: "Cuántos pases se vendieron y cuántos beneficiarios hay activos.",
    href: RUTAS.administracion.pases,
  },
  {
    bloque: "Equipos",
    pregunta: "Cuántas plantillas hay y cuántas están completas.",
    href: RUTAS.administracion.equipos,
  },
  {
    bloque: "Participantes",
    pregunta: "Cuántas personas hay y cuántas esperan cupo.",
    href: RUTAS.administracion.participantes,
  },
  {
    bloque: "Acreditaciones",
    pregunta: "Qué acreditación está activa y quién puede entrar a la fiesta.",
    href: RUTAS.administracion.pasesValidar,
  },
  {
    bloque: "Accesos",
    pregunta: "Qué accesos se registraron y cuáles fueron denegados.",
    href: RUTAS.administracion.validaciones,
  },
];

/**
 * ADM-01 - the operational summary of the edition.
 *
 * The summary is a reading surface: it never writes. Its content is the
 * edition in force and the eight blocks of metrics the backend publishes.
 */
export function AdminResumenView() {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-01"
        title="Estado operativo de la edición"
        description="El estado de la edición activa en un vistazo: inscripciones, pagos, cupos, pases, equipos, participantes, acreditaciones y accesos, con lo que requiere atención en primer lugar."
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
        description="Nombre de la edición, rango de fechas, fecha límite de modificación y si admite cambios."
      >
        <AdminEmptyState
          icon={LayoutDashboard}
          title="Todavía no hay una edición enlazada"
          description="El resumen se apoya en la edición activa que resuelve el backend. Cuando la integración esté disponible, aquí se verán su nombre, sus fechas, la fecha límite de modificación y si admite cambios."
        />
      </AdminPanel>

      <AdminPanel
        title="Bloques del resumen"
        description="Qué mide cada bloque del resumen y dónde se trabaja su detalle."
      >
        <AdminDataTable
          caption="Bloques del resumen operativo y su sección"
          columns={[
            { key: "bloque", label: "Bloque" },
            { key: "pregunta", label: "Qué responde" },
            { key: "seccion", label: "Sección" },
          ]}
          filas={BLOQUES.map((bloque) => ({
            cells: {
              bloque: <span className="font-medium text-foreground">{bloque.bloque}</span>,
              pregunta: (
                <span className="whitespace-normal text-muted-foreground">
                  {bloque.pregunta}
                </span>
              ),
              seccion: (
                <Link
                  href={bloque.href}
                  className="font-medium text-primary underline-offset-4 transition-colors hover:text-primary/80 hover:underline"
                >
                  Abrir sección
                </Link>
              ),
            },
          }))}
          vacio={
            <AdminEmptyState
              icon={Activity}
              title="Sin bloques publicados"
              description="El resumen no ha publicado ningún bloque para la edición activa."
            />
          }
        />
      </AdminPanel>
    </div>
  );
}
