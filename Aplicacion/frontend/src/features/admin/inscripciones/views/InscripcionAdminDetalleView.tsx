import { ClipboardList, History, ShoppingCart, UsersRound } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import {
  CifrasCupos,
  EsqueletoOperativo,
  ListaOperativa,
  MarcoOperativo,
  VeredictoConCausa,
  VeredictoOperativo,
} from "@/features/admin/operaciones";
import type {
  ColumnaOperativa,
  FilaOperativa,
} from "@/features/admin/operaciones";
import { RUTAS } from "@/lib/routes";
import { PanelPoolInscripcion } from "../components/PanelPoolInscripcion";
import type {
  AdminInscripcionDetalleOut,
  EstadoDetalleInscripcionAdmin,
} from "../types/inscripciones-admin.types";

const COLUMNAS_EQUIPOS: ColumnaOperativa[] = [
  { key: "equipo", label: "Equipo", prioridad: 1, titular: true },
  { key: "disciplina", label: "Disciplina", prioridad: 1 },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "participantes", label: "Participantes", prioridad: 2, numerico: true },
  { key: "estado_equipo", label: "Estado del equipo", prioridad: 2 },
];

const COLUMNAS_COMPRAS: ColumnaOperativa[] = [
  { key: "compra", label: "Compra", prioridad: 1, titular: true, identificador: true },
  { key: "estado", label: "Estado del pago", prioridad: 1 },
  { key: "total", label: "Total", prioridad: 2, numerico: true },
  { key: "moneda", label: "Moneda", prioridad: 2 },
  { key: "orden", label: "Orden de pago", prioridad: 2, identificador: true },
];

export interface InscripcionAdminDetalleViewProps {
  /** The identifier of the registration. */
  id: string;
  /** The state of the detail. The default is the honest one. */
  estado?: EstadoDetalleInscripcionAdmin;
}

/**
 * ADM-06 - `/administracion/inscripciones/[id]`.
 *
 * The detail is divided in the FIVE tabs of the plan (`frontend/04` §4):
 * Resumen · Equipos · Pool y personas · Compras de cupos · Historial. Every
 * tab has its OWN empty state, because a tab without data is not the same
 * fact as a screen without data (`SH-03` §5 · ADM-06).
 *
 * The page is READ ONLY apart from the withdrawal of a participant, which is
 * a S-10 action: it names its effect and asks for the reason.
 */
export function InscripcionAdminDetalleView({
  id,
  estado = { estado: "sin-datos" },
}: InscripcionAdminDetalleViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-06"
        title="Operar una inscripción"
        description="La ficha completa de una inscripción: equipos, participantes, compras de cupos, aceptaciones legales y saldo."
        meta={[{ etiqueta: "Inscripción", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.inscripciones}>
              Volver a las inscripciones
            </Link>
          </Button>
        }
      />

      <AdminNotice title="Acciones sensibles, efecto explícito">
        Retirar a una persona libera su cupo en esta inscripción y no genera
        devolución. Cada acción sensible pide confirmación con su efecto y un
        motivo que queda registrado.
      </AdminNotice>

      <Tabs defaultValue="resumen" className="gap-4">
        <TabsList className="min-h-11 max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="resumen" className="min-h-11 flex-none">
            Resumen
          </TabsTrigger>
          <TabsTrigger value="equipos" className="min-h-11 flex-none">
            Equipos
          </TabsTrigger>
          <TabsTrigger value="pool" className="min-h-11 flex-none">
            Pool y personas
          </TabsTrigger>
          <TabsTrigger value="compras" className="min-h-11 flex-none">
            Compras de cupos
          </TabsTrigger>
          <TabsTrigger value="historial" className="min-h-11 flex-none">
            Historial
          </TabsTrigger>
        </TabsList>

        <TabsContent value="resumen">
          <AdminPanel
            title="Resumen"
            description="Quién responde, qué paquete contrató y en qué estado está la inscripción."
          >
            <MarcoOperativo
              estado={estado}
              sinDatos={
                <AdminEmptyState
                  icon={ClipboardList}
                  title="No se pudo cargar esta inscripción"
                  description="El detalle se lee del servicio de administración, que todavía no expone su ruta. En cuanto exista, aquí se verán el responsable, el paquete, el estado y los tres cupos."
                />
              }
              cargando={<EsqueletoOperativo columnas={COLUMNAS_EQUIPOS} />}
            >
              {(datos: AdminInscripcionDetalleOut) => (
                <ResumenInscripcion datos={datos} />
              )}
            </MarcoOperativo>
          </AdminPanel>
        </TabsContent>

        <TabsContent value="equipos">
          <AdminPanel
            title="Equipos"
            description="Disciplina, plantilla y estado de cada equipo de la inscripción."
          >
            <MarcoOperativo
              estado={estado}
              sinDatos={
                <AdminEmptyState
                  icon={UsersRound}
                  title="No se pudieron cargar los equipos"
                  description="Los equipos de una inscripción se leen del servicio de administración, que todavía no expone su ruta."
                />
              }
              cargando={<EsqueletoOperativo columnas={COLUMNAS_EQUIPOS} />}
            >
              {(datos: AdminInscripcionDetalleOut) => (
                <ListaOperativa
                  caption="Equipos de la inscripción"
                  columnas={COLUMNAS_EQUIPOS}
                  filas={datos.equipos_detalle.map(
                    (equipo): FilaOperativa => ({
                      id: equipo.id,
                      celdas: {
                        equipo: equipo.nombre,
                        disciplina: equipo.disciplina.nombre,
                        estado: equipo.estado,
                        participantes: equipo.participantes.length,
                        estado_equipo: (
                          <VeredictoConCausa veredicto={equipo.estado_operativo} />
                        ),
                      },
                    }),
                  )}
                  vacio={
                    <AdminEmptyState
                      icon={UsersRound}
                      title="Sin equipos en esta inscripción"
                      description="Una inscripción puede no tener equipos todavía. Cuando el detalle esté conectado, aquí se listarán con su disciplina, su plantilla y su estado."
                    />
                  }
                />
              )}
            </MarcoOperativo>
          </AdminPanel>
        </TabsContent>

        <TabsContent value="pool">
          <AdminPanel
            title="Pool y personas"
            description="Los cupos de la inscripción, las causas que impiden ampliarla y las participaciones."
          >
            <MarcoOperativo
              estado={estado}
              sinDatos={
                <AdminEmptyState
                  icon={UsersRound}
                  title="No se pudo cargar el pool"
                  description="El pool se lee del servicio de administración, que todavía no expone su ruta."
                />
              }
              cargando={<EsqueletoOperativo columnas={COLUMNAS_EQUIPOS} />}
            >
              {(datos: AdminInscripcionDetalleOut) => (
                <PanelPoolInscripcion
                  pool={datos.pool}
                  inscripcionId={id}
                  personas={datos.equipos_detalle.flatMap((equipo) =>
                    equipo.participantes.map((participante) => ({
                      participante,
                      equipo: equipo.nombre,
                    })),
                  )}
                />
              )}
            </MarcoOperativo>
          </AdminPanel>
        </TabsContent>

        <TabsContent value="compras">
          <AdminPanel
            title="Compras de cupos"
            description="La compra inicial y las ampliaciones de cupos, con el estado de su pago."
          >
            <MarcoOperativo
              estado={estado}
              sinDatos={
                <AdminEmptyState
                  icon={ShoppingCart}
                  title="No se pudieron cargar las compras"
                  description="Las compras de cupos se leen del servicio de administración, que todavía no expone su ruta."
                />
              }
              cargando={<EsqueletoOperativo columnas={COLUMNAS_COMPRAS} />}
            >
              {(datos: AdminInscripcionDetalleOut) => (
                <ListaOperativa
                  caption="Compras de cupos de la inscripción"
                  columnas={COLUMNAS_COMPRAS}
                  filas={datos.compras.map(
                    (compra): FilaOperativa => ({
                      id: compra.compra_id,
                      celdas: {
                        compra: compra.compra_id,
                        estado: (
                          <VeredictoOperativo veredicto={compra.estado_operativo} />
                        ),
                        total: compra.total,
                        moneda: compra.moneda,
                        orden: compra.orden_pago_id ?? "—",
                      },
                    }),
                  )}
                  vacio={
                    <AdminEmptyState
                      icon={ShoppingCart}
                      title="Sin compras de cupos"
                      description="Esta inscripción todavía no amplió sus cupos. La compra inicial y las ampliaciones aparecerán aquí con su estado de pago."
                    />
                  }
                />
              )}
            </MarcoOperativo>
          </AdminPanel>
        </TabsContent>

        <TabsContent value="historial">
          <AdminPanel
            title="Historial"
            description="Los hechos registrados de esta inscripción, con su actor y su fecha."
          >
            <MarcoOperativo
              estado={estado}
              sinDatos={
                <AdminEmptyState
                  icon={History}
                  title="No se pudo cargar el historial"
                  description="El historial se lee del servicio de administración, que todavía no expone su ruta."
                />
              }
              cargando={<EsqueletoOperativo columnas={COLUMNAS_COMPRAS} />}
            >
              {(datos: AdminInscripcionDetalleOut) => (
                <ListaOperativa
                  caption="Historial de la inscripción"
                  columnas={[
                    { key: "fecha", label: "Fecha", prioridad: 1, titular: true },
                    { key: "tipo", label: "Hecho", prioridad: 1 },
                    { key: "descripcion", label: "Detalle", prioridad: 1 },
                    { key: "actor", label: "Actor", prioridad: 2 },
                  ]}
                  filas={datos.historial.map(
                    (evento): FilaOperativa => ({
                      id: `${evento.occurred_at}-${evento.tipo}`,
                      celdas: {
                        fecha: evento.occurred_at,
                        tipo: evento.tipo,
                        descripcion: evento.descripcion,
                        actor: evento.actor,
                      },
                    }),
                  )}
                  vacio={
                    <AdminEmptyState
                      icon={History}
                      title="Todavía no hay historial"
                      description="Los hechos de esta inscripción se registrarán aquí: su fecha, su tipo, su detalle y el actor que los produjo."
                    />
                  }
                />
              )}
            </MarcoOperativo>
          </AdminPanel>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * The tab «Resumen» of the detail.
 *
 * It shows the identity of the registration, its understandable state with
 * its cause and the THREE cupos, which are three different facts
 * (`GOV-02-RB-04a`).
 */
function ResumenInscripcion({ datos }: { datos: AdminInscripcionDetalleOut }) {
  return (
    <div className="flex flex-col gap-5">
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Dato etiqueta="Responsable" valor={datos.responsable.nombre} />
        <Dato etiqueta="Paquete" valor={datos.paquete.nombre} />
        <Dato etiqueta="Edición" valor={datos.edicion.nombre} />
      </dl>

      <VeredictoConCausa veredicto={datos.estado} />

      <CifrasCupos cupos={datos.cupos} />

      {datos.pago ? (
        <VeredictoConCausa veredicto={datos.pago} />
      ) : (
        <p className="text-sm text-muted-foreground">
          Esta inscripción todavía no tiene un pago asociado.
        </p>
      )}

      {datos.alerta ? (
        <p className="rounded-[var(--radius-md)] border border-warning/30 bg-warning/10 px-3 py-2 text-sm leading-snug text-foreground">
          {datos.alerta.mensaje}
        </p>
      ) : null}
    </div>
  );
}

/**
 * One fact of the summary, as a term of a definition list.
 */
function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-foreground-muted">{etiqueta}</dt>
      <dd className="text-sm font-medium text-foreground">{valor}</dd>
    </div>
  );
}
