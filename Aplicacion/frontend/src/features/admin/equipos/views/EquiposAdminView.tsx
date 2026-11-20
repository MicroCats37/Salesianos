import { UsersRound } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
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
} from "@/features/admin/operaciones";
import type {
  ColumnaOperativa,
  FilaOperativa,
  FiltroOperativo,
} from "@/features/admin/operaciones";
import { RUTAS } from "@/lib/routes";
import { PlantillaEquipo } from "../components/PlantillaEquipo";
import type {
  AdminEquipoListItemOut,
  EstadoListaEquiposAdmin,
} from "../types/equipos-admin.types";

/**
 * The columns of the list, in the order the plan asks for (`frontend/04` §5):
 * Equipo, disciplina/categoría, responsable, plantilla actual, mínimo
 * necesario, máximo, estado legible, motivo si no puede competir y acción
 * «Ver equipo».
 */
const COLUMNAS: ColumnaOperativa[] = [
  { key: "equipo", label: "Equipo", prioridad: 1, titular: true },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "plantilla", label: "Plantilla", prioridad: 1 },
  { key: "disciplina", label: "Disciplina", prioridad: 2 },
  { key: "categoria", label: "Categoría", prioridad: 2 },
  { key: "responsable", label: "Responsable", prioridad: 2 },
  { key: "inscripcion", label: "Inscripción", prioridad: 2 },
  { key: "accion", label: "Acción", prioridad: 2 },
];

/**
 * The filters of the list.
 *
 * `estado` uses the REAL lifecycle vocabulary of the target backend
 * (`EstadoEquipo`: `ACTIVO` and `RETIRADO`). The READINESS of a team —the
 * verdict that says whether it can compete— has no published catalogue yet,
 * so it is not offered as a filter with invented values.
 */
const FILTROS: FiltroOperativo[] = [
  {
    clave: "estado",
    etiqueta: "Estado del equipo",
    opciones: [
      { valor: "ACTIVO", etiqueta: "Activo" },
      { valor: "RETIRADO", etiqueta: "Retirado" },
    ],
  },
  {
    clave: "disciplina",
    etiqueta: "Disciplina",
    opciones: [],
    sinOpciones:
      "Las opciones llegan del catálogo de la edición; esta pantalla todavía no está conectada al servicio de administración.",
  },
];

/**
 * One row of the list.
 *
 * The name of the team opens its detail and its accessible name carries the
 * team AND its discipline, so the operator knows which record the link opens.
 */
function filaDe(equipo: AdminEquipoListItemOut): FilaOperativa {
  return {
    id: equipo.id,
    celdas: {
      equipo: (
        <Link
          href={RUTAS.administracion.equiposDetalle(equipo.id)}
          aria-label={`${equipo.nombre} · ${equipo.disciplina.nombre}`}
          className="font-semibold text-primary underline-offset-4 hover:underline"
        >
          {equipo.nombre}
        </Link>
      ),
      estado: <VeredictoConCausa veredicto={equipo.estado_operativo} />,
      plantilla: <PlantillaEquipo plantilla={equipo.plantilla} />,
      disciplina: equipo.disciplina.nombre,
      categoria: equipo.categoria.nombre,
      responsable: equipo.responsable.nombre,
      inscripcion: equipo.inscripcion.nombre,
      accion: (
        <Button variant="outline" size="sm" asChild className="min-h-11">
          <Link
            href={RUTAS.administracion.equiposDetalle(equipo.id)}
            aria-label={`Ver equipo ${equipo.nombre} · ${equipo.disciplina.nombre}`}
          >
            Ver equipo
          </Link>
        </Button>
      ),
    },
  };
}

export interface EquiposAdminViewProps {
  /** The state of the list. The default is the honest one. */
  estado?: EstadoListaEquiposAdmin;
  /** EVERY query parameter of the current URL. */
  parametros?: Record<string, string>;
}

/**
 * ADM-07 - `/administracion/equipos`.
 *
 * The list of the teams of the edition. It answers ONE question: whether a
 * team can compete, and WHY when it cannot. The reason is the
 * `descripcion` of the backend, printed next to the state; the browser never
 * infers the incompleteness from the roster (`contratos/01` §7).
 */
export function EquiposAdminView({
  estado = { estado: "sin-datos" },
  parametros = {},
}: EquiposAdminViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-07"
        title="Buscar y gestionar equipos"
        description="Las plantillas del evento con su disciplina, su categoría, su responsable, su roster y el veredicto de cada una."
      />

      <AdminNotice title="Dos hechos, no una fracción">
        El mínimo y el máximo deportivo son dos hechos independientes: el
        mínimo es lo que el equipo necesita para competir y el máximo es el
        tope duro de la disciplina. La capacidad y la completitud los deriva
        el servidor.
      </AdminNotice>

      <BusquedaOperativa
        parametros={parametros}
        etiqueta="Buscar equipo"
        placeholder="Nombre del equipo, responsable o disciplina"
      />

      <BarraFiltros
        filtros={FILTROS}
        parametros={parametros}
        etiqueta="Filtros de los equipos"
      />

      <AdminPanel
        title="Equipos"
        description="Plantillas del evento con su inscripción de origen."
      >
        <MarcoOperativo
          estado={estado}
          sinDatos={
            <AdminEmptyState
              icon={UsersRound}
              title="Todavía no hay equipos cargados"
              description="El listado de equipos se lee del servicio de administración, que todavía no expone su ruta. Cuando exista, aquí se listarán las plantillas con su disciplina, su roster y el veredicto de capacidad, con la búsqueda y los filtros."
            />
          }
          cargando={<EsqueletoOperativo columnas={COLUMNAS} />}
        >
          {(datos) => (
            <ListaOperativa
              caption="Equipos de la edición"
              columnas={COLUMNAS}
              filas={datos.map(filaDe)}
              vacio={
                <AdminEmptyState
                  icon={UsersRound}
                  title="No hay equipos para esta edición"
                  description="Todavía no se ha registrado ningún equipo. En cuanto exista uno, aparecerá aquí con su disciplina, su roster y el motivo por el que puede o no competir."
                />
              }
            />
          )}
        </MarcoOperativo>
      </AdminPanel>
    </div>
  );
}
