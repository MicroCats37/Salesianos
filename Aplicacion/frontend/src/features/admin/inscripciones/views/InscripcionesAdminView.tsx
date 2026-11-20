import { ClipboardList } from "lucide-react";
import Link from "next/link";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import {
  BarraFiltros,
  BusquedaOperativa,
  EsqueletoOperativo,
  ListaOperativa,
  MarcoOperativo,
  VeredictoConCausa,
  VeredictoOperativo,
} from "@/features/admin/operaciones";
import type {
  ColumnaOperativa,
  FilaOperativa,
  FiltroOperativo,
} from "@/features/admin/operaciones";
import { RUTAS } from "@/lib/routes";
import type {
  AdminInscripcionListItemOut,
  EstadoListaInscripcionesAdmin,
} from "../types/inscripciones-admin.types";

/**
 * The columns of the list, in the order the plan asks for (`frontend/04` §4):
 * responsable, paquete, edición, equipos, estado comprensible, cupos, pago
 * relevante y alerta.
 *
 * The priority of a column decides the WIDTH it appears at, never its
 * meaning: the essential columns survive at 768 and the rest arrive from
 * 1024 (`SH-02`).
 */
const COLUMNAS: ColumnaOperativa[] = [
  { key: "responsable", label: "Responsable", prioridad: 1, titular: true },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "cupos_disponibles", label: "Cupos disponibles", prioridad: 1, numerico: true },
  { key: "paquete", label: "Paquete", prioridad: 2 },
  { key: "edicion", label: "Edición", prioridad: 2 },
  { key: "equipos", label: "Equipos", prioridad: 2, numerico: true },
  { key: "personas", label: "Personas", prioridad: 2, numerico: true },
  { key: "cupos_adquiridos", label: "Cupos adquiridos", prioridad: 2, numerico: true },
  { key: "cupos_asignados", label: "Cupos asignados", prioridad: 2, numerico: true },
  { key: "pago", label: "Pago", prioridad: 2 },
  { key: "alerta", label: "Alerta", prioridad: 2 },
];

/**
 * The filters of the list.
 *
 * `estado` uses the REAL vocabulary of the target backend
 * (`EstadoInscripcion`: `CREADA` and `CANCELADA`). The filters whose option
 * catalogue is not published yet are shown DISABLED with the reason,
 * instead of a list of invented values.
 */
const FILTROS: FiltroOperativo[] = [
  {
    clave: "estado",
    etiqueta: "Estado",
    opciones: [
      { valor: "CREADA", etiqueta: "Creada" },
      { valor: "CANCELADA", etiqueta: "Cancelada" },
    ],
  },
  {
    clave: "disciplina",
    etiqueta: "Disciplina",
    opciones: [],
    sinOpciones:
      "Las opciones llegan del catálogo de la edición; esta pantalla todavía no está conectada al servicio de administración.",
  },
  {
    clave: "incidencia",
    etiqueta: "Incidencia",
    opciones: [],
    sinOpciones:
      "El catálogo de incidencias todavía no está publicado. Usa la búsqueda libre para filtrar por texto.",
  },
];

/**
 * One row of the list.
 *
 * The row opens the detail of the registration and its accessible name
 * carries the responsible AND the edition, so the operator knows which
 * record the link opens (`GOV-02-RB-03` · accessibility intent).
 */
function filaDe(inscripcion: AdminInscripcionListItemOut): FilaOperativa {
  return {
    id: inscripcion.id,
    celdas: {
      responsable: (
        <Link
          href={RUTAS.administracion.inscripcionesDetalle(inscripcion.id)}
          aria-label={`${inscripcion.responsable.nombre} · ${inscripcion.edicion.nombre}`}
          className="font-semibold text-primary underline-offset-4 hover:underline"
        >
          {inscripcion.responsable.nombre}
        </Link>
      ),
      estado: <VeredictoConCausa veredicto={inscripcion.estado} />,
      cupos_disponibles: inscripcion.cupos.disponibles,
      paquete: inscripcion.paquete.nombre,
      edicion: inscripcion.edicion.nombre,
      equipos: inscripcion.equipos,
      personas: inscripcion.personas,
      cupos_adquiridos: inscripcion.cupos.adquiridos,
      cupos_asignados: inscripcion.cupos.asignados,
      pago: inscripcion.pago ? (
        <VeredictoOperativo veredicto={inscripcion.pago} />
      ) : (
        <span className="text-foreground-muted">Sin dato de pago</span>
      ),
      alerta: inscripcion.alerta ? (
        <span className="text-sm leading-snug">{inscripcion.alerta.mensaje}</span>
      ) : (
        <span className="text-foreground-muted">—</span>
      ),
    },
  };
}

export interface InscripcionesAdminViewProps {
  /** The state of the list. The default is the honest one. */
  estado?: EstadoListaInscripcionesAdmin;
  /** EVERY query parameter of the current URL. */
  parametros?: Record<string, string>;
}

/**
 * ADM-05 - `/administracion/inscripciones`.
 *
 * The list of the registrations of the edition. It READS: it does not
 * validate, it does not reject and it does not release cupos. Every number
 * it shows is the number the server published.
 */
export function InscripcionesAdminView({
  estado = { estado: "sin-datos" },
  parametros = {},
}: InscripcionesAdminViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-05"
        title="Gestionar las inscripciones"
        description="Las inscripciones de la edición activa: quién las responde, qué paquete compraron, cuántas personas y equipos llevan y cuánto está pagado."
      />

      <AdminNotice title="Lectura, sin reescritura">
        La lista no valida, no rechaza ni libera cupos: publica el estado que
        calcula el backend. «Personas» y «Participaciones» son magnitudes
        distintas y la tabla las muestra por separado.
      </AdminNotice>

      <BusquedaOperativa
        parametros={parametros}
        etiqueta="Buscar inscripción"
        placeholder="Responsable, paquete o referencia"
      />

      <BarraFiltros
        filtros={FILTROS}
        parametros={parametros}
        etiqueta="Filtros de las inscripciones"
      />

      <AdminPanel
        title="Inscripciones"
        description="Registros de la edición activa con sus agregados operativos."
      >
        <MarcoOperativo
          estado={estado}
          sinDatos={
            <AdminEmptyState
              icon={ClipboardList}
              title="Todavía no hay inscripciones cargadas"
              description="El listado de inscripciones se lee del servicio de administración, que todavía no expone su ruta. Cuando exista, aquí se verán los registros con su responsable, su paquete y su estado."
            />
          }
          cargando={<EsqueletoOperativo columnas={COLUMNAS} />}
        >
          {(datos) => (
            <ListaOperativa
              caption="Inscripciones de la edición activa"
              columnas={COLUMNAS}
              filas={datos.map(filaDe)}
              vacio={
                <AdminEmptyState
                  icon={ClipboardList}
                  title="No hay inscripciones para esta edición"
                  description="Todavía no se ha registrado ninguna inscripción. En cuanto exista una, aparecerá aquí con su responsable, su estado y sus cupos."
                />
              }
            />
          )}
        </MarcoOperativo>
      </AdminPanel>
    </div>
  );
}
