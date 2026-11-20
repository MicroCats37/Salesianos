import {
  ArrowDown,
  ArrowUp,
  Eye,
  EyeOff,
  Handshake,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Button } from "@/components/ui/button";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import { ListaOperativa } from "@/features/admin/operaciones/components/ListaOperativa";
import type { ColumnaOperativa } from "@/features/admin/operaciones/types/operaciones.types";
import { FormularioPatrocinador } from "../components/FormularioPatrocinador";
import { GaleriaPatrocinador } from "../components/GaleriaPatrocinador";
import { LogoPatrocinador } from "../components/LogoPatrocinador";
import type { FormularioPatrocinadorDatos } from "../schemas/patrocinador.schema";
import { formularioPatrocinadorSchema } from "../schemas/patrocinador.schema";
import type {
  CodigoErrorMedio,
  EstadoVistaPatrocinadores,
  Patrocinador,
} from "../types/patrocinador.types";

/** The columns of the list of sponsors. */
const COLUMNAS: ColumnaOperativa[] = [
  { key: "patrocinador", label: "Patrocinador", titular: true },
  { key: "slug", label: "Identificador", identificador: true },
  { key: "edicion", label: "Edición", prioridad: 2 },
  { key: "visibilidad", label: "Visibilidad", prioridad: 2 },
  { key: "piezas", label: "Piezas", numerico: true },
  { key: "acciones", label: "Acciones" },
];

const VALORES_NUEVOS: FormularioPatrocinadorDatos = {
  nombre: "",
  slug: "",
  descripcion: "",
  sitio_web: "",
  visible: true,
  logo: null,
  imagenes: [],
};

export interface PatrocinadoresAdminViewProps {
  /** The state of the surface. */
  estado?: EstadoVistaPatrocinadores;
  /** The sponsors of the edition. */
  patrocinadores?: Patrocinador[];
  /** The sponsor whose pieces are open. */
  seleccionado?: Patrocinador;
  /** The media error the server declared, if it declared one. */
  errorMedio?: CodigoErrorMedio;
  /** The alta of a sponsor. */
  onCrear?: (datos: FormularioPatrocinadorDatos) => void | Promise<void>;
  /** The edition of a sponsor. */
  onActualizar?: (
    datos: FormularioPatrocinadorDatos,
    patrocinador: Patrocinador,
  ) => void | Promise<void>;
  /** The opening of the pieces of ONE sponsor. */
  onSeleccionar?: (patrocinador: Patrocinador) => void;
  /** The deletion of ONE sponsor. */
  onEliminar?: (patrocinador: Patrocinador) => void;
  /** The movement of ONE sponsor up in the gallery. */
  onSubir?: (patrocinador: Patrocinador) => void;
  /** The movement of ONE sponsor down in the gallery. */
  onBajar?: (patrocinador: Patrocinador) => void;
  /** Whether an operation is in flight. */
  ocupado?: boolean;
}

/**
 * PatrocinadoresAdminView - `ADM-21`, the sponsors and their pieces.
 *
 * A sponsor is an ally with a name, a logo, an ordered gallery and a
 * visibility. It has NO monetary field: no contribution, no commission and
 * no amount (`GOV-02-RB-08b`, `frontend/04` §9).
 *
 * The record is edited in the modal of the area (`AppFormModal`), the same
 * way every other record of the console is edited.
 */
export function PatrocinadoresAdminView({
  estado = "sin-datos",
  patrocinadores = [],
  seleccionado,
  errorMedio,
  onCrear,
  onActualizar,
  onSeleccionar,
  onEliminar,
  onSubir,
  onBajar,
  ocupado = false,
}: PatrocinadoresAdminViewProps) {
  const [modalAbierto, setModalAbierto] = useState(false);
  const [enEdicion, setEnEdicion] = useState<Patrocinador | null>(null);

  const visibles = patrocinadores.filter(
    (patrocinador) => patrocinador.visible,
  );
  const piezas = patrocinadores.reduce(
    (total, patrocinador) => total + patrocinador.imagenes.length,
    0,
  );

  const abrirNuevo = () => {
    setEnEdicion(null);
    setModalAbierto(true);
  };

  const abrirEdicion = (patrocinador: Patrocinador) => {
    onSeleccionar?.(patrocinador);
    setEnEdicion(patrocinador);
    setModalAbierto(true);
  };

  const cerrar = () => {
    setModalAbierto(false);
    setEnEdicion(null);
  };

  const valoresIniciales: FormularioPatrocinadorDatos = enEdicion
    ? {
        nombre: enEdicion.nombre,
        slug: enEdicion.slug,
        descripcion: enEdicion.descripcion,
        sitio_web: enEdicion.sitio_web,
        visible: enEdicion.visible,
        logo: null,
        imagenes: [],
      }
    : VALORES_NUEVOS;

  return (
    <>
      <div className="flex flex-col gap-6">
        <AdminPageHeader
          pageId="ADM-21"
          title="Gestionar patrocinadores y sus piezas"
          description="Los aliados de la edición y las piezas que aportan: marca, presencia en la web y material impreso."
          meta={[
            { etiqueta: "Patrocinadores", valor: patrocinadores.length },
            { etiqueta: "Visibles", valor: visibles.length },
            { etiqueta: "Piezas", valor: piezas },
          ]}
          actions={
            <Button type="button" onClick={abrirNuevo}>
              <Plus className="size-4" aria-hidden="true" />
              Nuevo patrocinador
            </Button>
          }
        />

        <AdminNotice title="Un patrocinador no tiene cifras">
          La ficha de un patrocinador guarde su nombre, su logo, su galería
          ordenada y su visibilidad. No tiene cifras ni importes: eso no existe
          en el contrato del patrocinador.
        </AdminNotice>

        {estado === "cargando" ? (
          <div role="status" aria-live="polite" className="flex flex-col gap-3">
            <span className="sr-only">Cargando los patrocinadores…</span>
            <div className="flex flex-col gap-4">
              <div className="h-24 w-full rounded-[var(--radius-lg)] bg-surface-raised" />
              <div className="h-24 w-full rounded-[var(--radius-lg)] bg-surface-raised" />
            </div>
          </div>
        ) : estado === "sin-permiso" ? (
          <ShellPermissionDenied title="No tienes permiso para gestionar patrocinadores" />
        ) : estado === "error" ? (
          <ShellErrorState
            title="No pudimos cargar los patrocinadores"
            description="El servidor no devolvió la lista. Puedes volver a intentarlo; si el problema continúa, revisa la edición activa."
            accion={{ label: "Reintentar" }}
          />
        ) : estado !== "listo" ? (
          <AdminPanel
            title="Patrocinadores"
            description="Los aliados registrados, con su logo y su galería ordenada."
          >
            <AdminEmptyState
              icon={Handshake}
              title="Todavía no hay patrocinadores que mostrar"
              description="El servicio de patrocinadores todavía no está disponible en el backend, así que aquí no se dibuja ninguna ficha. Cuando lo esté, se listarán con su logo, con su galería ordenada y con su visibilidad, y se podrá dar de alta un patrocinador nuevo."
            />
          </AdminPanel>
        ) : (
          <>
            <AdminPanel
              title="Patrocinadores"
              description="Los aliados registrados, con su logo, su galería y su visibilidad."
            >
              <ListaOperativa
                caption="Patrocinadores de la edición"
                columnas={COLUMNAS}
                vacio={
                  <AdminEmptyState
                    icon={Handshake}
                    title="Todavía no hay patrocinadores en la edición"
                    description="Cuando se registre el primer patrocinador, aquí se listarán con su logo, su galería ordenada y su visibilidad."
                  />
                }
                filas={patrocinadores.map((patrocinador) => ({
                  id: patrocinador.id,
                  celdas: {
                    patrocinador: (
                      <span className="flex items-center gap-3">
                        <LogoPatrocinador
                          logo={patrocinador.logo}
                          nombre={patrocinador.nombre}
                          decorativo
                        />
                        <span className="font-medium text-foreground">
                          {patrocinador.nombre}
                        </span>
                      </span>
                    ),
                    slug: (
                      <span className="font-mono text-xs text-muted-foreground">
                        {patrocinador.slug}
                      </span>
                    ),
                    edicion: (
                      <span className="text-muted-foreground">
                        {patrocinador.edicion_nombre}
                      </span>
                    ),
                    visibilidad: (
                      <span className="inline-flex items-center gap-1.5 text-sm text-foreground">
                        {patrocinador.visible ? (
                          <Eye
                            className="size-3.5 text-success"
                            aria-hidden="true"
                          />
                        ) : (
                          <EyeOff
                            className="size-3.5 text-foreground-muted"
                            aria-hidden="true"
                          />
                        )}
                        {patrocinador.visible ? "Visible" : "Oculto"}
                      </span>
                    ),
                    piezas: String(patrocinador.imagenes.length),
                    acciones: (
                      <div className="flex flex-wrap items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => abrirEdicion(patrocinador)}
                          aria-label={`Editar ${patrocinador.nombre}`}
                        >
                          <Pencil className="size-4" aria-hidden="true" />
                          Editar
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => onSubir?.(patrocinador)}
                          aria-label={`Subir ${patrocinador.nombre} en la galería`}
                        >
                          <ArrowUp className="size-4" aria-hidden="true" />
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => onBajar?.(patrocinador)}
                          aria-label={`Bajar ${patrocinador.nombre} en la galería`}
                        >
                          <ArrowDown className="size-4" aria-hidden="true" />
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => onEliminar?.(patrocinador)}
                          aria-label={`Eliminar ${patrocinador.nombre}`}
                        >
                          <Trash2
                            className="size-4 text-destructive"
                            aria-hidden="true"
                          />
                        </Button>
                      </div>
                    ),
                  },
                }))}
              />
            </AdminPanel>

            <AdminPanel
              title="Pieza del patrocinador"
              description="El logo de identidad y la galería ordenada de las piezas publicadas."
            >
              {seleccionado ? (
                <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <p className="text-caption text-muted-foreground">
                      Logo de identidad
                    </p>
                    <LogoPatrocinador
                      logo={seleccionado.logo}
                      nombre={seleccionado.nombre}
                      className="w-24"
                    />
                  </div>
                  <div className="flex flex-col gap-2">
                    <p className="text-caption text-muted-foreground">
                      Galería ordenada
                    </p>
                    <GaleriaPatrocinador imagenes={seleccionado.imagenes} />
                  </div>
                </div>
              ) : (
                <AdminEmptyState
                  icon={Handshake}
                  title="No hay ninguna pieza abierta"
                  description="Abre un patrocinador de la lista para ver su logo y su galería ordenada."
                />
              )}
            </AdminPanel>
          </>
        )}
      </div>

      <AppFormModal<FormularioPatrocinadorDatos>
        key={enEdicion?.id ?? "nuevo"}
        open={modalAbierto}
        onOpenChange={(abierto) => {
          if (!abierto) cerrar();
        }}
        title={enEdicion ? `Editar ${enEdicion.nombre}` : "Nuevo patrocinador"}
        eyebrow="Patrocinadores"
        icon={<Handshake className="size-5" aria-hidden="true" />}
        description="El nombre, el identificador en la edición, la descripción, el sitio web, la visibilidad y las piezas publicadas."
        primaryLabel={
          enEdicion ? "Guardar los cambios" : "Guardar el patrocinador"
        }
        primaryLoadingLabel="Guardando…"
        primaryLoading={ocupado}
        primaryDisabled={!enEdicion && !onCrear}
        onPrimary={() => undefined}
        schema={formularioPatrocinadorSchema}
        initialData={valoresIniciales}
        onSubmit={async (datos) => {
          if (enEdicion) {
            await onActualizar?.(datos, enEdicion);
          } else {
            await onCrear?.(datos);
          }
          cerrar();
        }}
        bodyClassName="max-h-[70vh] overflow-y-auto"
      >
        {({ methods }) => (
          <div className="flex flex-col gap-5">
            {!onCrear ? (
              <p className="text-caption text-muted-foreground">
                El servicio de patrocinadores todavía no está conectado en el
                backend: el formulario se puede completar, pero el guardado no
                sale de este dispositivo.
              </p>
            ) : null}
            <FormularioPatrocinador
              methods={methods}
              errorMedio={errorMedio}
              ocupado={ocupado}
            />
          </div>
        )}
      </AppFormModal>
    </>
  );
}
