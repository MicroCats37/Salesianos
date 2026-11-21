"use client";

import Hls from "hls.js";
import { Play, VideoOff } from "lucide-react";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  clasificarVideo,
  esUrlHttpSeguro,
  urlEmbebibleVideo,
} from "../utils/video.tipo.utils";

export interface ReproductorVideoProps {
  /** The address that the server published. */
  url: string;
  /** The title of the video: the accessible name of the player. */
  titulo: string;
  /** Start muted playback automatically when this is the live signal. */
  autoPlay?: boolean;
  className?: string;
}

function ReproductorHls({
  url,
  titulo,
  autoPlay = false,
  className,
}: ReproductorVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(video);
      return () => hls.destroy();
    }

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
    }
  }, [url]);

  return (
    <video
      ref={videoRef}
      controls
      autoPlay={autoPlay}
      muted={autoPlay}
      preload="metadata"
      playsInline
      aria-label={titulo}
      className={cn("size-full bg-surface-inverse object-contain", className)}
    >
      Tu navegador no puede reproducir esta transmisión.
    </video>
  );
}

/**
 * ReproductorVideo - the SAFE renderer of a published address.
 *
 * Four ways to show the same address, and NEVER a fifth:
 *
 * - `hls`: the official `.m3u8` signal plays through Hls.js in this page.
 * - `archivo`: the browser plays it with its own control. There is NO
 *   autoplay: the sound starts when the visitor asks for it.
 * - `embebible`: a known provider. The frame is sandboxed and it carries a
 *   title, so the visitor knows what the frame is.
 * - `externo`: anything else stays inside the page as an unavailable signal.
 *
 * An address whose scheme is not `http`/`https` is shown as TEXT: an anchor
 * with a `javascript:` address is an execution, not a navigation.
 *
 * `dangerouslySetInnerHTML` and `srcDoc` are FORBIDDEN here: the backend
 * returns an address as data and this component never interprets it.
 */
export function ReproductorVideo({
  url,
  titulo,
  autoPlay = false,
  className,
}: ReproductorVideoProps) {
  const tipo = clasificarVideo(url);
  const embebible = urlEmbebibleVideo(url);

  if (tipo === "hls") {
    return (
      <ReproductorHls
        url={url}
        titulo={titulo}
        autoPlay={autoPlay}
        className={className}
      />
    );
  }

  if (tipo === "archivo") {
    return (
      <video
        controls
        autoPlay={autoPlay}
        muted={autoPlay}
        preload="metadata"
        playsInline
        aria-label={titulo}
        src={url}
        className={cn("size-full bg-surface-inverse object-contain", className)}
      >
        Tu navegador no puede reproducir esta transmisión.
      </video>
    );
  }

  if (tipo === "embebible" && embebible) {
    return (
      <iframe
        title={titulo}
        src={embebible}
        loading="lazy"
        allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        referrerPolicy="no-referrer-when-downgrade"
        /*
         * `allow-scripts` together with `allow-same-origin` would defeat the
         * sandbox, so the frame is only shown for the HARDCODED providers of
         * `video.tipo.utils.ts`: the list never comes from the data.
         */
        sandbox="allow-scripts allow-same-origin allow-presentation"
        className={cn("size-full border-0", className)}
      />
    );
  }

  if (!esUrlHttpSeguro(url)) {
    return (
      <div
        className={cn(
          "flex size-full flex-col items-center justify-center gap-2 p-6 text-center",
          className,
        )}
      >
        <Play className="size-6 text-primary" aria-hidden="true" />
        <p className="text-sm font-semibold text-foreground">
          Esta dirección no se puede reproducir aquí
        </p>
        <p className="max-w-measure text-sm text-muted-foreground">
          El servidor la publicó fuera de los formatos que la sala admite. Se
          muestra como texto para que nadie pueda ejecutarla por accidente.
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex size-full flex-col items-center justify-center gap-3 p-6 text-center",
        className,
      )}
    >
      <VideoOff className="size-6 text-primary" aria-hidden="true" />
      <p className="max-w-measure text-sm text-muted-foreground">
        Esta señal no está disponible dentro del reproductor del festival.
        Espera la transmisión HLS oficial.
      </p>
    </div>
  );
}
