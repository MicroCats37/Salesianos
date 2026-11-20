"use client";

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { handleApiError } from "@/errors";
import type { VideoListItem } from "@/features/videos/schemas/video.schema";
import {
  useActualizarVideoAdmin,
  useCrearVideoAdmin,
  useEliminarVideoAdmin,
  useListaVideosAdmin,
} from "../hooks/useAdminVideos";
import type { CrearVideoFormData } from "../schemas/admin.video.schema";
import type { EstadoListaVideosAdmin } from "../types/admin.video.types";
import { AdminVideosView } from "./AdminVideosView";

export interface AdminVideosRutaProps {
  /** EVERY query parameter of the current URL. */
  parametros: Record<string, string>;
}

/** The size of the page of the administration list. */
const TAMANO_PAGINA = 25;

/**
 * ADM-21 - the container of `/administracion/videos`.
 *
 * The filters live in the URL (`GOV-02-RB-03b`): the page reads the query
 * string and this container writes it back. The browser never filters the
 * gallery on its own — the search travels to the SERVER and the server
 * answers with the page that belongs to it.
 *
 * The container owns the reads, the writes and the state of the two
 * dialogues. The VIEW owns the drawing.
 */
export function AdminVideosRuta({ parametros }: AdminVideosRutaProps) {
  const router = useRouter();
  const pathname = usePathname();

  const [editorAbierto, setEditorAbierto] = useState(false);
  const [videoEnEdicion, setVideoEnEdicion] = useState<VideoListItem | null>(
    null,
  );
  const [videoAEliminar, setVideoAEliminar] = useState<VideoListItem | null>(
    null,
  );
  const [errorEliminacion, setErrorEliminacion] = useState<string | null>(null);

  const busqueda = parametros.q?.trim() ?? "";
  const paginaLeida = Number(parametros.page ?? "1");
  const pagina =
    Number.isFinite(paginaLeida) && paginaLeida > 0 ? paginaLeida : 1;

  const lista = useListaVideosAdmin({
    q: busqueda.length > 0 ? busqueda : undefined,
    page: pagina,
    page_size: TAMANO_PAGINA,
  });

  const crear = useCrearVideoAdmin();
  const actualizar = useActualizarVideoAdmin();
  const eliminar = useEliminarVideoAdmin();

  const error = lista.error ? handleApiError(lista.error) : null;

  const estado: EstadoListaVideosAdmin = lista.isPending
    ? "cargando"
    : error
      ? error.status === 403
        ? "sin-permiso"
        : "error"
      : "listo";

  const escribirUrl = (nuevos: Record<string, string | undefined>) => {
    const consulta = new URLSearchParams();

    for (const [clave, valor] of Object.entries(nuevos)) {
      if (valor) consulta.set(clave, valor);
    }

    const cadena = consulta.toString();

    router.push(cadena ? `${pathname}?${cadena}` : pathname);
  };

  const buscar = (texto: string) => {
    escribirUrl({ q: texto.trim() || undefined, page: undefined });
  };

  const cambiarPagina = (nuevaPagina: number) => {
    escribirUrl({
      q: busqueda.length > 0 ? busqueda : undefined,
      page: nuevaPagina > 1 ? String(nuevaPagina) : undefined,
    });
  };

  const abrirNuevo = () => {
    setVideoEnEdicion(null);
    setEditorAbierto(true);
  };

  const abrirEdicion = (video: VideoListItem) => {
    setVideoEnEdicion(video);
    setEditorAbierto(true);
  };

  const cerrarEditor = () => {
    setEditorAbierto(false);
    setVideoEnEdicion(null);
  };

  const abrirEliminacion = (video: VideoListItem) => {
    setErrorEliminacion(null);
    setVideoAEliminar(video);
  };

  const cerrarEliminacion = () => {
    setVideoAEliminar(null);
    setErrorEliminacion(null);
  };

  /**
   * The publication or the edition.
   *
   * It REJECTS when the server refuses, so the form receives the field errors
   * of the answer and puts each one next to the control that owns it.
   */
  const guardar = async (datos: CrearVideoFormData) => {
    if (videoEnEdicion) {
      await actualizar.mutateAsync({ id: videoEnEdicion.id, datos });
    } else {
      await crear.mutateAsync(datos);
    }

    cerrarEditor();
  };

  const confirmarEliminacion = async () => {
    if (!videoAEliminar) return;

    setErrorEliminacion(null);

    try {
      await eliminar.mutateAsync(videoAEliminar.id);
      setVideoAEliminar(null);
    } catch (fallo) {
      setErrorEliminacion(handleApiError(fallo).message);
    }
  };

  const ocupado =
    lista.isPending ||
    crear.isPending ||
    actualizar.isPending ||
    eliminar.isPending;

  return (
    <AdminVideosView
      estado={estado}
      videos={lista.data?.items}
      total={lista.data?.total}
      pagina={lista.data?.page ?? pagina}
      totalPaginas={lista.data?.total_pages ?? 1}
      busqueda={busqueda}
      mensajeError={error?.message}
      reintentar={() => void lista.refetch()}
      onBuscar={buscar}
      onCambiarPagina={cambiarPagina}
      onNuevo={abrirNuevo}
      onEditar={abrirEdicion}
      onEliminar={abrirEliminacion}
      editorAbierto={editorAbierto}
      videoEnEdicion={videoEnEdicion ?? undefined}
      onCerrarEditor={cerrarEditor}
      onGuardar={guardar}
      ocupado={ocupado}
      videoAEliminar={videoAEliminar ?? undefined}
      onCerrarEliminacion={cerrarEliminacion}
      onConfirmarEliminacion={() => void confirmarEliminacion()}
      errorEliminacion={errorEliminacion ?? undefined}
    />
  );
}
