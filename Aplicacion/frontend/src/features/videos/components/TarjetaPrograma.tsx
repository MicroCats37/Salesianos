"use client";

import { ArrowUpRight, Play, Radio } from "lucide-react";
import Link from "next/link";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import type { VideoListItem } from "../types/video.types";
import { clasificarVideo } from "../utils/video.tipo.utils";

export interface TarjetaProgramaProps {
  /** The published signal of the board. */
  video: VideoListItem;
  className?: string;
}

const MESES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

/**
 * The day a video was published.
 *
 * The date is formatted in UTC with an explicit calendar: the server and the
 * browser must say the SAME day, or the page would change under the visitor
 * when it hydrates.
 */
function fechaPublicada(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";

  return `${fecha.getUTCDate()} de ${MESES[fecha.getUTCMonth()]} de ${fecha.getUTCFullYear()}`;
}

/**
 * TarjetaPrograma - one line of the published board.
 *
 * The board is a CARTELERA, not a wall of frames: every published signal is
 * the same address without a poster, so the row lets the title, the copy and
 * the day carry the weight instead of a picture that the server never sent.
 */
export function TarjetaPrograma({ video, className }: TarjetaProgramaProps) {
  const enVivo = clasificarVideo(video.url) === "hls";
  const publicado = fechaPublicada(video.created_at);

  return (
    <Link
      href={RUTAS.publico.videoDetalle(video.id)}
      className={cn(
        "group flex gap-4 py-5 transition-colors hover:bg-surface-recessed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:gap-5 sm:px-4",
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-full border transition-colors",
          enVivo
            ? "border-destructive/40 bg-destructive/10 text-destructive"
            : "border-border bg-surface text-primary",
          "group-hover:border-primary/40",
        )}
      >
        {enVivo ? <Radio className="size-5" /> : <Play className="size-5" />}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h3 className="font-heading text-base font-bold text-foreground sm:text-lg">
            {video.titulo}
          </h3>
          {enVivo ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-destructive/10 px-2 py-0.5 text-eyebrow-brand text-destructive">
              <span className="size-1.5 rounded-full bg-destructive" />
              En vivo
            </span>
          ) : null}
        </div>

        {video.descripcion ? (
          <p className="mt-1 line-clamp-2 max-w-measure text-sm text-muted-foreground">
            {video.descripcion}
          </p>
        ) : null}

        {publicado ? (
          <p className="mt-2 text-caption text-muted-foreground">
            Publicado el {publicado}
          </p>
        ) : null}
      </div>

      <span className="hidden shrink-0 items-center gap-1 self-center text-caption font-semibold text-primary sm:inline-flex">
        Ver
        <ArrowUpRight className="size-4" aria-hidden="true" />
      </span>
    </Link>
  );
}
