import { Handshake } from "lucide-react";
import {
  AdminEmptyState,
  AdminNotice,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import {
  ShellErrorState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { Skeleton } from "@/components/ui/skeleton";
import { FormularioPatrocinador } from "../components/FormularioPatrocinador";
import type { DatosPatrocinador } from "../components/FormularioPatrocinador";
import { GaleriaPatrocinador } from "../components/GaleriaPatrocinador";
import { LogoPatrocinador } from "../components/LogoPatrocinador";
import { TablaPatrocinadores } from "../components/TablaPatrocinadores";
import type {
  CodigoErrorMedio,
  EstadoVistaPatrocinadores,
  Patrocinador,
} from "../types/patrocinador.types";

/**
 * PatrocinadoresAdminView - `ADM-21`, the sponsors and their pieces.
 *
 * A sponsor is an ally with a name, a logo, an ordered gallery and a
 * visibility. It has NO monetary field: no contribution, no commission and
 * no amount (`GOV-02-RB-08b`, `frontend/04` §9).
 *
 * The gallery is the memorable surface of the route: it is a wall of pieces
 * with an order, and the rest of the screen stays quiet.
 */
export function PatrocinadoresAdminView({
  estado = "sin-datos",
  patrocinadores = [],
  seleccionado,
  errorMedio,
  onGuardar,
  ocupado = false,
}: {
  estado?: EstadoVistaPatrocinadores;
  patrocinadores?: Patrocinador[];
  /** The sponsor whose record is open. */
  seleccionado?: Patrocinador;
  /** The media error the server declared, if it declared one. */
  errorMedio?: CodigoErrorMedio;
  /** The save of the record. */
  onGuardar?: (datos: DatosPatrocinador) => void;
  /** Whether an operation is in flight. */
  ocupado?: boolean;
}) {
  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-21"
        title="Gestionar patrocinadores y sus piezas"
        description="Los aliados de la edición y las piezas que aportan: marca, presencia en la web y material impreso."
      />

      <AdminNotice title="Un patrocinador no tiene cifras">
        La ficha de un patrocinador guarde su nombre, su logo, su galería
        ordenada y su visibilidad. No tiene aportaciones, comisiones ni
        importes: eso no existe en el contrato del patrocinador.
      </AdminNotice>

      {estado === "cargando" ? (
        <div role="status" aria-live="polite" className="flex flex-col gap-3">
          <span className="sr-only">Cargando los patrocinadores…</span>
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
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
            <TablaPatrocinadores patrocinadores={patrocinadores} />
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

          <AdminPanel
            title="Ficha del patrocinador"
            description="El nombre, el identificador, la descripción, el sitio web y la visibilidad."
          >
            <FormularioPatrocinador
              patrocinador={seleccionado}
              errorMedio={errorMedio}
              onGuardar={onGuardar}
              ocupado={ocupado}
            />
          </AdminPanel>
        </>
      )}
    </div>
  );
}
