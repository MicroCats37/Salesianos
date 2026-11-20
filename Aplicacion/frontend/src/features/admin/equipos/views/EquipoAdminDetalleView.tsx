"use client";

import { ShieldCheck, UserPlus, UserRoundCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  ModalAgregarParticipante,
  useAgregarParticipanteEquipo,
} from "@/features/admin/asistido";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import type {
  AccionOperativa,
  ColumnaOperativa,
  FilaOperativa,
} from "@/features/admin/operaciones";
import {
  CifrasCupos,
  EsqueletoOperativo,
  ExplicacionVeredicto,
  ListaOperativa,
  MarcoOperativo,
  VeredictoConCausa,
} from "@/features/admin/operaciones";
import { RUTAS } from "@/lib/routes";
import { PanelPlantillaEquipo } from "../components/PanelPlantillaEquipo";
import type {
  AdminEquipoDetalleOut,
  EstadoDetalleEquipoAdmin,
} from "../types/equipos-admin.types";

const COLUMNAS_ELEGIBILIDAD: ColumnaOperativa[] = [
  { key: "persona", label: "Persona", prioridad: 1, titular: true },
  { key: "documento", label: "Documento", prioridad: 1 },
  { key: "veredicto", label: "Elegibilidad", prioridad: 1 },
];

/**
 * The vocabulary of the actions of this route.
 *
 * The LABEL is the vocabulary of this interface; the CODE is the one the
 * presenter publishes in `acciones_disponibles`. The projection decides
 * whether the affordance is SHOWN; it never authorises it, and the 403 of
 * the backend remains the control (`GOV-02-RB-03d`).
 */
const ACCIONES: readonly AccionOperativa[] = [
  { codigo: "AGREGAR_PARTICIPANTE", etiqueta: "Agregar jugador" },
  { codigo: "VER_PARTICIPANTES", etiqueta: "Ver participantes" },
];

export interface EquipoAdminDetalleViewProps {
  /** The identifier of the team. */
  id: string;
  /** The state of the detail. The default is the honest one. */
  estado?: EstadoDetalleEquipoAdmin;
}

/**
 * ADM-08 - `/administracion/equipos/[id]`.
 *
 * The operational view of ONE team: its identity, the state with its reason,
 * the roster with the document and the state of every person, the related
 * registration, the related cupos, the eligibility of the candidates and the
 * authorised actions.
 *
 * `frontend/04` §5: the operator understands the readiness of the team
 * without opening a console. Every reason comes from the backend.
 */
export function EquipoAdminDetalleView({
  id,
  estado = { estado: "sin-datos" },
}: EquipoAdminDetalleViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-08"
        title="Operar un equipo: plantilla y elegibilidad"
        description="La nómina de un equipo y las personas que todavía podrían entrar en él, con el motivo de cada bloqueo."
        meta={[{ etiqueta: "Equipo", valor: id }]}
        actions={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={RUTAS.administracion.equipos}>
              Volver a los equipos
            </Link>
          </Button>
        }
      />

      <AdminNotice title="El veredicto lo dice el servidor">
        La elegibilidad de una persona y la razón por la que un equipo puede o
        no competir los decide el backend. Aquí se reproduce su veredicto con su
        etiqueta y su descripción; nunca se calcula en el navegador.
      </AdminNotice>

      <MarcoOperativo
        estado={estado}
        sinDatos={
          <AdminEmptyState
            icon={UserRoundCheck}
            title="No se pudo cargar este equipo"
            description="El detalle del equipo se lee del servicio de administración, que todavía no expone su ruta. En cuanto exista, aquí se verán su estado con su motivo, su plantilla, sus cupos y la elegibilidad de los candidatos."
          />
        }
        cargando={<EsqueletoOperativo columnas={COLUMNAS_ELEGIBILIDAD} />}
      >
        {(datos: AdminEquipoDetalleOut) => <DetalleEquipo datos={datos} />}
      </MarcoOperativo>
    </div>
  );
}

/**
 * The composition of the detail of a team.
 */
function DetalleEquipo({ datos }: { datos: AdminEquipoDetalleOut }) {
  const [modalAgregar, setModalAgregar] = useState(false);
  const agregar = useAgregarParticipanteEquipo();

  const accionesVisibles = ACCIONES.filter((accion) =>
    datos.acciones_disponibles.includes(accion.codigo),
  );

  const agregarParticipante = (
    <Button
      type="button"
      variant="outline"
      className="min-h-11"
      onClick={() => setModalAgregar(true)}
    >
      <UserPlus className="size-4" aria-hidden="true" />
      Agregar participante
    </Button>
  );

  return (
    <div className="flex flex-col gap-6">
      <AdminPanel
        title="Identidad y estado"
        description="Quién responde, en qué disciplina compite y por qué puede o no competir."
        actions={agregarParticipante}
      >
        <div className="flex flex-col gap-5">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Dato etiqueta="Equipo" valor={datos.nombre} />
            <Dato etiqueta="Disciplina" valor={datos.disciplina.nombre} />
            <Dato etiqueta="Categoría" valor={datos.categoria?.nombre ?? "—"} />
            <Dato etiqueta="Responsable" valor={datos.responsable.nombre} />
            <Dato
              etiqueta="Inscripción"
              valor={datos.inscripcion_detalle.nombre}
            />
            <Dato
              etiqueta="Referencia"
              valor={datos.inscripcion_detalle.referencia}
            />
          </dl>

          <ExplicacionVeredicto veredicto={datos.estado_operativo} />

          {accionesVisibles.length > 0 ? (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-semibold text-foreground">
                Acciones autorizadas
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                {accionesVisibles.map((accion) => (
                  <Button
                    key={accion.codigo}
                    variant="outline"
                    className="min-h-11"
                    disabled
                  >
                    <ShieldCheck className="size-4" aria-hidden="true" />
                    {accion.etiqueta}
                  </Button>
                ))}
              </div>
              <p className="text-xs leading-snug text-muted-foreground">
                Las acciones aparecen porque el backend las proyecta, pero no se
                pueden ejecutar todavía: su endpoint no está registrado.
              </p>
            </div>
          ) : null}
        </div>
      </AdminPanel>

      <AdminPanel
        title="Plantilla"
        description="Las personas que ya integran el equipo, con su documento y su estado."
        actions={agregarParticipante}
      >
        <PanelPlantillaEquipo
          participantes={datos.participantes}
          inscripcionId={datos.inscripcion_detalle.id}
        />
      </AdminPanel>

      <AdminPanel
        title="Cupos de la inscripción"
        description="Los tres cupos de la inscripción a la que pertenece este equipo."
      >
        <CifrasCupos cupos={datos.cupos} />
      </AdminPanel>

      <AdminPanel
        title="Elegibilidad"
        description="Las personas que el backend considera asignables a este equipo y el motivo de las que no lo son."
      >
        <ListaOperativa
          caption="Elegibilidad de las personas para este equipo"
          columnas={COLUMNAS_ELEGIBILIDAD}
          filas={datos.elegibilidad.map(
            (candidato): FilaOperativa => ({
              id: candidato.id,
              celdas: {
                persona: candidato.nombre,
                documento: candidato.documento,
                veredicto: (
                  <VeredictoConCausa veredicto={candidato.estado_operativo} />
                ),
              },
            }),
          )}
          vacio={
            <AdminEmptyState
              icon={UserRoundCheck}
              title="La elegibilidad la decide el backend"
              description="La lista de candidatos con su veredicto —asignable, motivo del bloqueo o disciplinas ya cubiertas— llega del servidor. El navegador no pre-valida a nadie: reproduce el veredicto."
            />
          }
        />
      </AdminPanel>

      <ModalAgregarParticipante
        open={modalAgregar}
        onOpenChange={setModalAgregar}
        equipoNombre={datos.nombre}
        agregando={agregar.isPending}
        onAgregar={async (datosFormulario) => {
          await agregar.mutateAsync({
            equipoId: datos.id,
            payload: {
              tipo_documento: datosFormulario.tipo_documento,
              numero_documento: datosFormulario.numero_documento,
              rol: datosFormulario.rol,
              motivo: datosFormulario.motivo,
            },
          });
          setModalAgregar(false);
        }}
      />
    </div>
  );
}

/**
 * One fact of the identity, as a term of a definition list.
 */
function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-foreground-muted">{etiqueta}</dt>
      <dd className="text-sm font-medium text-foreground">{valor}</dd>
    </div>
  );
}
