"use client";

import { Pencil, Trash2 } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AdminDataTable } from "@/features/admin/components";
import type { VideoListItem } from "@/features/videos/schemas/video.schema";

export interface AdminVideosTablaProps {
  /** The videos of the administration list. */
  videos: VideoListItem[];
  /** The action that opens the editor with this video. */
  onEditar: (video: VideoListItem) => void;
  /** The action that opens the confirmation of the deletion. */
  onEliminar: (video: VideoListItem) => void;
  /** Whether the area is waiting for the server. */
  ocupado?: boolean;
  /** What the table shows when the list is empty. */
  vacio?: ReactNode;
}

/**
 * The day a video was published.
 *
 * The date is formatted in UTC with an explicit calendar: the server and the
 * browser must say the SAME day, or the page would change under the operator
 * when it hydrates.
 */
function fechaPublicada(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";

  const meses = [
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
  ];

  return `${String(fecha.getUTCDate()).padStart(2, "0")} ${meses[fecha.getUTCMonth()]} ${fecha.getUTCFullYear()}`;
}

/**
 * AdminVideosTabla - the list of the published videos.
 *
 * The table is the OPERATIONAL view of the gallery: the title, the address
 * that the visitor will open, the day it was published and the two actions
 * of the operator.
 *
 * The address is shown as TEXT and never as a link: it is data that the
 * operator typed, and the operator decides when it opens.
 */
export function AdminVideosTabla({
  videos,
  onEditar,
  onEliminar,
  ocupado = false,
  vacio,
}: AdminVideosTablaProps) {
  const columnas = [
    { key: "titulo", label: "Título" },
    { key: "url", label: "Dirección" },
    { key: "publicado", label: "Publicado", numerico: true },
    { key: "acciones", label: "Acciones" },
  ];

  const filas = videos.map((video) => ({
    cells: {
      titulo: (
        <span className="flex flex-col gap-0.5">
          <span className="font-semibold text-foreground">{video.titulo}</span>
          {video.descripcion ? (
            <span className="text-xs text-muted-foreground">
              {video.descripcion}
            </span>
          ) : null}
        </span>
      ),
      url: (
        <span className="font-mono text-xs break-all text-muted-foreground">
          {video.url}
        </span>
      ),
      publicado: (
        <span className="text-sm text-muted-foreground">
          {fechaPublicada(video.created_at)}
        </span>
      ),
      acciones: (
        <span className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11"
            disabled={ocupado}
            onClick={() => onEditar(video)}
          >
            <Pencil className="size-4" aria-hidden="true" />
            Editar
            <span className="sr-only"> {video.titulo}</span>
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11 text-destructive"
            disabled={ocupado}
            onClick={() => onEliminar(video)}
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Eliminar
            <span className="sr-only"> {video.titulo}</span>
          </Button>
        </span>
      ),
    },
  }));

  return (
    <AdminDataTable
      caption="Los videos publicados en la sala de proyección"
      columns={columnas}
      filas={filas}
      vacio={vacio}
    />
  );
}
