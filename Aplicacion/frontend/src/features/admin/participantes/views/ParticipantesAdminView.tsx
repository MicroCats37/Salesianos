import { Search, Users } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import type {
  ColumnaOperativa,
  FilaOperativa,
} from "@/features/admin/operaciones";
import {
  BusquedaOperativa,
  EsqueletoOperativo,
  ListaOperativa,
  MarcoOperativo,
} from "@/features/admin/operaciones";
import type {
  EstadoParticipantesAdmin,
  ParticipacionAdminOut,
  ParticipanteAdminOut,
} from "../types/participantes-admin.types";

/**
 * The three groupings of the plan (`frontend/04` §5): by event, by team and
 * by discipline. The axis of the grouping opens the row and the rest of the
 * facts follow it.
 */
const COLUMNAS_EVENTO: ColumnaOperativa[] = [
  { key: "edicion", label: "Edición", prioridad: 1, titular: true },
  { key: "persona", label: "Persona", prioridad: 1 },
  { key: "equipo", label: "Equipo", prioridad: 1 },
  { key: "disciplina", label: "Disciplina", prioridad: 1 },
  { key: "estado", label: "Estado", prioridad: 2 },
  { key: "conflicto", label: "Conflicto", prioridad: 2 },
];

const COLUMNAS_EQUIPO: ColumnaOperativa[] = [
  { key: "equipo", label: "Equipo", prioridad: 1, titular: true },
  { key: "persona", label: "Persona", prioridad: 1 },
  { key: "edicion", label: "Edición", prioridad: 1 },
  { key: "disciplina", label: "Disciplina", prioridad: 1 },
  { key: "estado", label: "Estado", prioridad: 2 },
  { key: "conflicto", label: "Conflicto", prioridad: 2 },
];

const COLUMNAS_DISCIPLINA: ColumnaOperativa[] = [
  { key: "disciplina", label: "Disciplina", prioridad: 1, titular: true },
  { key: "persona", label: "Persona", prioridad: 1 },
  { key: "edicion", label: "Edición", prioridad: 1 },
  { key: "equipo", label: "Equipo", prioridad: 1 },
  { key: "estado", label: "Estado", prioridad: 2 },
  { key: "conflicto", label: "Conflicto", prioridad: 2 },
];

/**
 * One participation as a row.
 *
 * The conflict is the `mensaje` of the backend, printed verbatim: a conflict
 * is a FACT with a reason, never a red highlight that only the colour
 * carries (`GOV-02-RB-04b` · accessibility intent of `RB-04`).
 */
function filaDe(
  participacion: ParticipacionAdminOut,
  persona: ParticipanteAdminOut,
): FilaOperativa {
  return {
    id: participacion.id,
    celdas: {
      persona: (
        <span className="flex flex-col">
          <span className="font-semibold text-foreground">
            {persona.nombre}
          </span>
          <span className="text-xs text-foreground-muted">
            {persona.documento}
          </span>
        </span>
      ),
      edicion: participacion.edicion.nombre,
      equipo: participacion.equipo.nombre,
      disciplina: participacion.disciplina.nombre,
      estado: participacion.estado,
      conflicto: participacion.conflicto ? (
        <span className="text-sm leading-snug">
          {participacion.conflicto.mensaje}
        </span>
      ) : (
        <span className="text-foreground-muted">—</span>
      ),
    },
  };
}

/**
 * Every participation of every person of the result, with the person it
 * belongs to.
 */
function participacionesDe(
  personas: readonly ParticipanteAdminOut[],
): { participacion: ParticipacionAdminOut; persona: ParticipanteAdminOut }[] {
  return personas.flatMap((persona) =>
    persona.participaciones.map((participacion) => ({
      participacion,
      persona,
    })),
  );
}

export interface ParticipantesAdminViewProps {
  /** The state of the search. The default is the honest one. */
  estado?: EstadoParticipantesAdmin;
  /** EVERY query parameter of the current URL. */
  parametros?: Record<string, string>;
}

/**
 * ADM-09 - `/administracion/participantes`.
 *
 * The search of people and their participations. It does NOT duplicate the
 * administration of accounts: it answers the sporting question —who plays
 * where and whether something collides— and leaves the account panel to its
 * own route.
 *
 * The prompt comes FIRST: until the operator searches, the page says what to
 * search and why, instead of showing an empty table (`RB-04` · state S-02).
 */
export function ParticipantesAdminView({
  estado = { estado: "sin-datos" },
  parametros = {},
}: ParticipantesAdminViewProps) {
  const hayBusqueda = (parametros.q ?? "").trim() !== "";

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-09"
        title="Buscar personas y participaciones"
        description="Dos superficies distintas: las personas registradas en el evento y las filas de roster que cada disciplina ha cerrado."
      />

      <AdminNotice title="Dos magnitudes, no una">
        Las dos listas nunca se reconcilian en el navegador. Un cupo pagado
        habilita a una persona en todas las disciplinas contratadas, así que
        «personas» y «participaciones» son recuentos distintos por construcción.
      </AdminNotice>

      <BusquedaOperativa
        parametros={parametros}
        etiqueta="Buscar por documento o nombre"
        placeholder="Documento o nombre de la persona"
      />

      {!hayBusqueda ? (
        <AdminEmptyState
          icon={Search}
          title="Busca a una persona para empezar"
          description="Escribe un documento o un nombre arriba. Verás sus participaciones por evento, equipo y disciplina, los conflictos que el backend detectó y su historial."
        />
      ) : (
        <MarcoOperativo
          estado={estado}
          sinDatos={
            <AdminEmptyState
              icon={Search}
              title="No se pudo cargar esta búsqueda"
              description="La búsqueda de participaciones se lee del servicio de administración, que todavía no expone su ruta. En cuanto exista, aquí se listarán las personas con sus participaciones y el motivo de cada conflicto."
            />
          }
          cargando={<EsqueletoOperativo columnas={COLUMNAS_EVENTO} />}
        >
          {(personas) => (
            <AdminPanel
              title="Participaciones"
              description="Cada fila es una participación: la persona, el evento, el equipo, la disciplina y el estado."
            >
              <Tabs defaultValue="evento" className="gap-4">
                <TabsList className="min-h-11 max-w-full justify-start overflow-x-auto">
                  <TabsTrigger value="evento" className="min-h-11 flex-none">
                    Por evento
                  </TabsTrigger>
                  <TabsTrigger value="equipo" className="min-h-11 flex-none">
                    Por equipo
                  </TabsTrigger>
                  <TabsTrigger
                    value="disciplina"
                    className="min-h-11 flex-none"
                  >
                    Por disciplina
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="evento">
                  <ListaOperativa
                    caption="Participaciones agrupadas por evento"
                    columnas={COLUMNAS_EVENTO}
                    filas={participacionesDe(personas).map(
                      ({ participacion, persona }) =>
                        filaDe(participacion, persona),
                    )}
                    vacio={
                      <AdminEmptyState
                        icon={Users}
                        title="Sin participaciones para esta búsqueda"
                        description="La persona no tiene participaciones en esta edición, o todavía no se han publicado. En cuanto existan, aparecerán aquí con su equipo, su disciplina y su estado."
                      />
                    }
                  />
                </TabsContent>

                <TabsContent value="equipo">
                  <ListaOperativa
                    caption="Participaciones agrupadas por equipo"
                    columnas={COLUMNAS_EQUIPO}
                    filas={participacionesDe(personas).map(
                      ({ participacion, persona }) =>
                        filaDe(participacion, persona),
                    )}
                    vacio={
                      <AdminEmptyState
                        icon={Users}
                        title="Sin participaciones para esta búsqueda"
                        description="La persona no tiene participaciones en esta edición, o todavía no se han publicado."
                      />
                    }
                  />
                </TabsContent>

                <TabsContent value="disciplina">
                  <ListaOperativa
                    caption="Participaciones agrupadas por disciplina"
                    columnas={COLUMNAS_DISCIPLINA}
                    filas={participacionesDe(personas).map(
                      ({ participacion, persona }) =>
                        filaDe(participacion, persona),
                    )}
                    vacio={
                      <AdminEmptyState
                        icon={Users}
                        title="Sin participaciones para esta búsqueda"
                        description="La persona no tiene participaciones en esta edición, o todavía no se han publicado."
                      />
                    }
                  />
                </TabsContent>
              </Tabs>
            </AdminPanel>
          )}
        </MarcoOperativo>
      )}
    </div>
  );
}
