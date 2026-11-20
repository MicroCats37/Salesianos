"use client";

import { Clapperboard, Plus, Search } from "lucide-react";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AdminEmptyState,
  AdminPageHeader,
  AdminPanel,
} from "@/features/admin/components";
import type { VideoListItem } from "@/features/videos/schemas/video.schema";
import { AdminVideoEditor } from "../components/AdminVideoEditor";
import { AdminVideosTabla } from "../components/AdminVideosTabla";
import type { CrearVideoFormData } from "../schemas/admin.video.schema";
import type { EstadoListaVideosAdmin } from "../types/admin.video.types";

export interface AdminVideosViewProps {
  /** The state of the list. */
  estado?: EstadoListaVideosAdmin;
  /** The videos of the administration list. */
  videos?: VideoListItem[];
  /** The total that the server published. */
  total?: number;
  /** The page that the server answered. */
  pagina?: number;
  /** The pages that the server published. */
  totalPaginas?: number;
  /** The search that is active in the URL. */
  busqueda?: string;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the server
   * chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
  /** The action that writes the search in the URL. */
  onBuscar: (texto: string) => void;
  /** The action that writes the page in the URL. */
  onCambiarPagina: (pagina: number) => void;
  /** The action that opens the editor for a new video. */
  onNuevo: () => void;
  /** The action that opens the editor with an existing video. */
  onEditar: (video: VideoListItem) => void;
  /** The action that opens the confirmation of the deletion. */
  onEliminar: (video: VideoListItem) => void;
  /** Whether the editor is open. */
  editorAbierto?: boolean;
  /** The video that the editor is editing. */
  videoEnEdicion?: VideoListItem;
  /** The action that closes the editor. */
  onCerrarEditor: () => void;
  /** The publication of the video. */
  onGuardar: (datos: CrearVideoFormData) => Promise<void>;
  /** Whether the area is waiting for the server. */
  ocupado?: boolean;
  /** The video whose deletion waits for the confirmation. */
  videoAEliminar?: VideoListItem;
  /** The action that closes the confirmation. */
  onCerrarEliminacion: () => void;
  /** The action that deletes the video. */
  onConfirmarEliminacion: () => void;
  /** The message of a failed deletion. */
  errorEliminacion?: string;
}

/**
 * ADM-21 - the administration of the gallery of videos.
 *
 * The area follows the OPERATIONAL system of the panel: a header, a block
 * with a table and the two actions of the operator. The expressive direction
 * belongs to the PUBLIC side: here the video is a record, not a poster.
 */
export function AdminVideosView({
  estado = "listo",
  videos = [],
  total = 0,
  pagina = 1,
  totalPaginas = 1,
  busqueda = "",
  mensajeError,
  reintentar,
  onBuscar,
  onCambiarPagina,
  onNuevo,
  onEditar,
  onEliminar,
  editorAbierto = false,
  videoEnEdicion,
  onCerrarEditor,
  onGuardar,
  ocupado = false,
  videoAEliminar,
  onCerrarEliminacion,
  onConfirmarEliminacion,
  errorEliminacion,
}: AdminVideosViewProps) {
  const hayBusqueda = busqueda.trim().length > 0;

  return (
    <div className="flex flex-col gap-6">
      <AdminPageHeader
        pageId="ADM-21"
        title="Videos de la sala de proyección"
        description="La galería que el público ve en /videos. Cada video es un título, una descripción y una dirección: lo que el servidor publica es lo que se muestra."
        meta={[{ etiqueta: "Videos", valor: String(total) }]}
        actions={
          <Button className="min-h-11" onClick={onNuevo} disabled={ocupado}>
            <Plus className="size-4" aria-hidden="true" />
            Publicar un video
          </Button>
        }
      />

      <AdminPanel
        title="Galería publicada"
        description="Los videos que la sala de proyección muestra ahora mismo."
      >
        <div className="flex flex-col gap-4">
          <form
            key={busqueda}
            className="flex flex-col gap-2 sm:flex-row sm:items-center"
            onSubmit={(evento) => {
              evento.preventDefault();
              const datos = new FormData(evento.currentTarget);
              onBuscar(String(datos.get("q") ?? ""));
            }}
          >
            <label htmlFor="videos-busqueda" className="sr-only">
              Buscar videos por título o descripción
            </label>
            <Input
              id="videos-busqueda"
              name="q"
              type="search"
              defaultValue={busqueda}
              placeholder="Buscar por título o descripción"
              className="min-h-11 sm:max-w-md"
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button type="submit" variant="outline" className="min-h-11">
                <Search className="size-4" aria-hidden="true" />
                Buscar
              </Button>
              {hayBusqueda ? (
                <Button
                  type="button"
                  variant="ghost"
                  className="min-h-11"
                  onClick={() => onBuscar("")}
                >
                  Limpiar
                </Button>
              ) : null}
            </div>
          </form>

          {estado === "sin-permiso" ? (
            <ShellPermissionDenied
              title="No tienes permiso para gestionar los videos"
              description="Tu cuenta no tiene la capacidad necesaria para abrir esta sección. Si crees que es un error, contacta con la organización del evento."
            />
          ) : null}

          {estado === "cargando" ? (
            <ShellPendingState
              title="Cargando la galería"
              description="Estamos leyendo los videos publicados."
            />
          ) : null}

          {estado === "error" ? (
            <ShellErrorState
              title="No pudimos cargar la galería"
              description={
                mensajeError ??
                "No pudimos leer los videos en este momento. Vuelve a intentarlo en unos segundos."
              }
              accion={
                reintentar
                  ? { label: "Reintentar", onClick: reintentar }
                  : undefined
              }
            />
          ) : null}

          {estado === "listo" ? (
            <AdminVideosTabla
              videos={videos}
              onEditar={onEditar}
              onEliminar={onEliminar}
              ocupado={ocupado}
              vacio={
                hayBusqueda ? (
                  <AdminEmptyState
                    icon={Search}
                    title="Ningún video coincide con la búsqueda"
                    description="Prueba con otras palabras o quita el filtro para ver la galería completa."
                    action={
                      <Button
                        type="button"
                        variant="outline"
                        className="min-h-11"
                        onClick={() => onBuscar("")}
                      >
                        Quitar el filtro
                      </Button>
                    }
                  />
                ) : (
                  <AdminEmptyState
                    icon={Clapperboard}
                    title="Todavía no hay videos publicados"
                    description="La galería pública está vacía. Publica el primer video y aparecerá en la sala de proyección."
                    action={
                      <Button className="min-h-11" onClick={onNuevo}>
                        <Plus className="size-4" aria-hidden="true" />
                        Publicar un video
                      </Button>
                    }
                  />
                )
              }
            />
          ) : null}

          {estado === "listo" && totalPaginas > 1 ? (
            <nav
              aria-label="Páginas de la galería"
              className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4"
            >
              <p className="text-sm text-muted-foreground">
                Página {pagina} de {totalPaginas} · {total} videos
              </p>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="min-h-11"
                  disabled={pagina <= 1 || ocupado}
                  onClick={() => onCambiarPagina(pagina - 1)}
                >
                  Anterior
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="min-h-11"
                  disabled={pagina >= totalPaginas || ocupado}
                  onClick={() => onCambiarPagina(pagina + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </nav>
          ) : null}
        </div>
      </AdminPanel>

      <AdminVideoEditor
        abierto={editorAbierto}
        onAbiertoChange={(abierto) => {
          if (!abierto) onCerrarEditor();
        }}
        video={videoEnEdicion}
        ocupado={ocupado}
        onGuardar={onGuardar}
      />

      <AlertDialog
        open={Boolean(videoAEliminar)}
        onOpenChange={(abierto) => {
          if (!abierto) onCerrarEliminacion();
        }}
      >
        <AlertDialogContent className="sm:max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar el video</AlertDialogTitle>
            <AlertDialogDescription>
              {videoAEliminar
                ? `«${videoAEliminar.titulo}» desaparece de la sala de proyección y deja de estar visible para el público. Esta acción no se puede deshacer.`
                : "El video desaparece de la sala de proyección y deja de estar visible para el público. Esta acción no se puede deshacer."}
            </AlertDialogDescription>
          </AlertDialogHeader>

          {errorEliminacion ? (
            <p role="alert" className="text-sm text-destructive">
              {errorEliminacion}
            </p>
          ) : null}

          <AlertDialogFooter>
            <AlertDialogCancel className="min-h-11">Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="min-h-11"
              disabled={ocupado}
              onClick={(evento) => {
                evento.preventDefault();
                onConfirmarEliminacion();
              }}
            >
              {ocupado ? "Eliminando…" : "Eliminar el video"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
