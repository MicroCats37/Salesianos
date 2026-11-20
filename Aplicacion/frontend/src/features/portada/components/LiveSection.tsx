"use client";

import { ArrowUpRight, Play } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { handleApiError } from "@/errors";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { FESTIVAL } from "@/features/portada/fixtures/festival";
import { TarjetaVideo } from "@/features/videos/components/TarjetaVideo";
import { useVideosLista } from "@/features/videos/hooks/useVideos";

/**
 * Sección "06 / TRANSMISIÓN EN VIVO".
 *
 * Es la entrada pública a las señales de partidos y del evento.
 */
export function LiveSection() {
  const videos = useVideosLista();
  const error = videos.error ? handleApiError(videos.error) : null;
  const destacados = videos.data ?? [];

  return (
    <PortadaSection
      id="en-vivo"
      eyebrow={COPY.enVivo.eyebrow}
      titulo={[...COPY.enVivo.titulo]}
      destacado={COPY.enVivo.destacado}
      copy={COPY.enVivo.copy}
    >
      <div className="mt-12 grid gap-10 lg:grid-cols-2 lg:items-center lg:gap-14">
        <div className="relative overflow-hidden rounded-2xl border border-primary/10 shadow-xl shadow-primary/10">
          <div className="relative aspect-[16/10] w-full">
            <Image
              src="/images/portada/futbol.png"
              alt="Imagen deportiva del programa del festival"
              fill
              loading="lazy"
              sizes="(max-width: 1024px) 100vw, 50vw"
              className="object-cover"
            />
          </div>
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-t from-brand-deep-navy/85 via-brand-deep-navy/25 to-transparent"
          />
          <span className="absolute top-4 left-4 inline-flex items-center gap-2 rounded-full bg-brand-deep-night/45 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-surface-inverse-foreground backdrop-blur-sm">
            <span
              className="size-1.5 rounded-full bg-accent"
              aria-hidden="true"
            />
            {COPY.enVivo.estado}
          </span>
          <Link
            href="#transmisiones-publicadas"
            aria-label="Ir a las transmisiones publicadas"
            className="absolute inset-0 m-auto grid size-16 place-items-center rounded-full bg-surface-raised/90 text-primary shadow-xl transition-transform hover:scale-105"
          >
            <Play className="size-7 fill-current" aria-hidden="true" />
          </Link>
          <div className="absolute inset-x-0 bottom-0 p-5">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-cyan">
              {FESTIVAL.nombre}
            </p>
            <p className="mt-1 text-sm font-bold uppercase tracking-wide text-surface-inverse-foreground">
              EL FESTIVAL TAMBIÉN SE VIVE A DISTANCIA.
            </p>
          </div>
        </div>

        <div>
          <p className="text-sm leading-relaxed text-muted-foreground sm:text-base">
            {COPY.enVivo.nota}
          </p>
          <Link
            href="#transmisiones-publicadas"
            className="mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
          >
            VER SEÑALES PUBLICADAS
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </div>

      <div id="transmisiones-publicadas" className="mt-10" data-portada-stagger>
        {videos.isPending ? (
          <p className="text-sm text-muted-foreground">
            Cargando las señales oficiales...
          </p>
        ) : null}

        {error ? (
          <p className="text-sm text-destructive">{error.message}</p>
        ) : null}

        {!videos.isPending && !error && destacados.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Las señales oficiales aparecerán aquí cuando inicien los partidos y
            actividades del festival.
          </p>
        ) : null}

        {destacados.length > 0 ? (
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {destacados.map((video) => (
              <li key={video.id}>
                <TarjetaVideo video={video} />
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </PortadaSection>
  );
}
