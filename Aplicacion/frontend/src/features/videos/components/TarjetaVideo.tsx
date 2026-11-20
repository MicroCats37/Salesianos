"use client";

import { Play } from "lucide-react";
import Link from "next/link";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import type { VideoListItem } from "../types/video.types";
import { clasificarVideo } from "../utils/video.tipo.utils";

export interface TarjetaVideoProps {
  /** The video of the gallery. */
  video: VideoListItem;
  className?: string;
}

/**
 * The label that names the way the address is shown.
 *
 * It is PRESENTATION: the visitor knows how the video will open before it
 * opens.
 */
function etiquetaDeTipo(tipo: ReturnType<typeof clasificarVideo>): string {
  switch (tipo) {
    case "hls":
      return "En vivo";
    case "archivo":
      return "Transmisión";
    case "embebible":
      return "Transmisión";
    default:
      return "Ver transmisión";
  }
}

/**
 * TarjetaVideo - one published event transmission.
 *
 * The card is a SCREEN: it keeps the 16:9 shape of the stage of the detail,
 * so the grid reads as a wall of screens and not as a list of links.
 *
 * The card does NOT embed the video: a wall of frames would download a wall
 * of players before the visitor chose one. The stage opens in the detail.
 */
export function TarjetaVideo({ video, className }: TarjetaVideoProps) {
  const tipo = clasificarVideo(video.url);

  return (
    <article
      className={cn(
        "flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface-raised shadow-[var(--elevation-sm)] transition-shadow duration-(--motion-duration-base) hover:shadow-[var(--elevation-md)]",
        className,
      )}
    >
      <Link
        href={RUTAS.publico.videoDetalle(video.id)}
        className="flex flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <div className="relative aspect-video w-full overflow-hidden bg-surface-inverse">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-hero-gradient opacity-90"
          />
          <span className="absolute inset-0 flex items-center justify-center">
            <span className="flex size-12 items-center justify-center rounded-full border border-brand-on-gradient-border bg-brand-on-gradient/15 text-brand-on-gradient">
              <Play className="size-5" aria-hidden="true" />
            </span>
          </span>
          <span className="absolute bottom-2 left-2 rounded-full bg-surface-inverse/80 px-2 py-0.5 text-eyebrow-brand text-surface-inverse-foreground">
            {etiquetaDeTipo(tipo)}
          </span>
        </div>

        <div className="flex flex-1 flex-col gap-2 p-4">
          <h2 className="font-heading text-base leading-snug font-semibold text-foreground">
            {video.titulo}
          </h2>
          {video.descripcion ? (
            <p className="line-clamp-3 text-sm text-muted-foreground">
              {video.descripcion}
            </p>
          ) : null}
        </div>
      </Link>
    </article>
  );
}
