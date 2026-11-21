import { ArrowLeft, Clapperboard, Radio, Tv } from "lucide-react";
import Link from "next/link";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { RUTAS } from "@/lib/routes";
import { PatrocinadoresVideoBanner } from "../components/PatrocinadoresVideoBanner";
import { ReproductorVideo } from "../components/ReproductorVideo";
import { TarjetaPrograma } from "../components/TarjetaPrograma";
import type { EstadoVistaVideos, VideoListItem } from "../types/video.types";

const SENAL_PRINCIPAL = "https://salesianosfest.pe/live/studio-1/index.m3u8";

export interface VideosListaViewProps {
  /** The state of the gallery. */
  estado?: EstadoVistaVideos;
  /** The videos of the gallery. */
  videos?: VideoListItem[];
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the server
   * chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}

/**
 * VID-01 - the public gallery of videos.
 *
 * The route speaks the same visual language as the landing: the same surface,
 * the same gold rule, the same two-column split and the same rhythm between
 * sections. The screen is the protagonist; the archive frames it.
 *
 * The gallery waits for the server: it never fills itself with example videos,
 * because a poster that the server did not publish is a promise that the
 * server cannot keep.
 */
export function VideosListaView({
  estado = "sin-datos",
  videos = [],
  mensajeError,
  reintentar,
}: VideosListaViewProps) {
  const sinVideos = estado === "listo" && videos.length === 0;

  return (
    <div className="relative left-1/2 -mx-4 -mt-10 w-screen -translate-x-1/2 sm:-mx-6 sm:-mt-12 lg:-mx-10 lg:-mt-10">
      <PortadaSection
        id="transmisiones"
        fondo="pagina"
        altura="auto"
        className="py-10 sm:py-14 lg:py-16"
        contenidoClassName="max-w-[var(--container-wide)]"
      >
        <div className="flex flex-col gap-10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link
              href={RUTAS.publico.inicio}
              className="inline-flex min-h-11 items-center gap-2 rounded-full border border-border bg-surface-raised px-4 text-sm font-semibold text-foreground transition-[transform,background-color] duration-(--motion-duration-base) hover:-translate-y-0.5 hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring active:translate-y-0"
            >
              <ArrowLeft className="size-4" aria-hidden="true" />
              Volver a la portada
            </Link>

            <span className="inline-flex items-center gap-2 text-caption text-muted-foreground">
              <Tv className="size-4" aria-hidden="true" />
              Salesianos Fest
            </span>
          </div>

          <div className="flex flex-col gap-4">
            <span
              className="rule-gold mb-3 block h-0.5 w-10 rounded-full"
              aria-hidden="true"
            />
            <p className="text-eyebrow-brand">
              Salesianos Fest · Transmisión oficial
            </p>
            <h1 className="mt-3 font-heading text-3xl font-black uppercase leading-[1.05] tracking-tight text-foreground sm:text-4xl">
              El festival en directo
            </h1>
            <p className="mt-4 max-w-measure text-lead text-muted-foreground">
              Los partidos, las finales y la fiesta, en una sola pantalla y con
              el sonido de la casa.
            </p>
          </div>

          <div className="mx-auto w-full max-w-5xl">
            <div className="overflow-hidden rounded-[var(--radius-2xl)] border border-border bg-surface-inverse shadow-[var(--elevation-lg)]">
              <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b border-brand-on-gradient-border px-4 py-2.5 sm:px-5">
                <span className="inline-flex items-center gap-2 text-eyebrow-brand text-brand-on-gradient">
                  <span
                    className="size-2 animate-[var(--animate-pulse-slow)] rounded-full bg-destructive"
                    aria-hidden="true"
                  />
                  En directo
                </span>
                <span className="inline-flex items-center gap-2 text-caption text-brand-on-gradient-muted">
                  <Radio className="size-4" aria-hidden="true" />
                  Señal oficial
                </span>
              </div>
              <div className="aspect-video w-full bg-surface-inverse">
                <ReproductorVideo
                  url={SENAL_PRINCIPAL}
                  titulo="Transmisión en vivo de Salesianos Fest"
                  autoPlay
                />
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-6">
            <p className="text-eyebrow-brand text-muted-foreground">
              Con el apoyo de
            </p>
            <PatrocinadoresVideoBanner transparente className="mt-2" />
          </div>
        </div>
      </PortadaSection>

      <PortadaSection
        id="cartelera"
        eyebrow="ARCHIVO / TRANSMISIONES"
        titulo={["CARTELERA", "DE", "TRANSMISIONES."]}
        destacado="TRANSMISIONES."
        copy="Las señales que ya se han emitido quedan archivadas aquí. Abre una para verla completa."
        fondo="pagina"
        altura="auto"
        className="py-10 sm:py-14 lg:py-16"
        contenidoClassName="max-w-[var(--container-wide)]"
      >
        <div className="mt-10 flex flex-col gap-8">
          {estado === "sin-permiso" ? (
            <ShellPermissionDenied
              title="No podemos mostrar las transmisiones"
              description="La señal no está disponible para ti ahora mismo."
              className="border-border bg-surface-raised"
            />
          ) : null}

          {estado === "cargando" ? (
            <ShellPendingState
              title="Conectando con las transmisiones"
              description="Estamos preparando los partidos y el evento."
            />
          ) : null}

          {estado === "error" ? (
            <ShellErrorState
              title="No pudimos cargar las transmisiones"
              description={
                mensajeError ??
                "No pudimos conectar con las transmisiones en este momento. Vuelve a intentarlo en unos segundos."
              }
              accion={
                reintentar
                  ? { label: "Reintentar", onClick: reintentar }
                  : undefined
              }
            />
          ) : null}

          {estado === "sin-datos" ? (
            <RouteEmptyState
              icon={Clapperboard}
              title="Las transmisiones todavía no están disponibles"
              description="Aquí aparecerán las señales oficiales de los partidos y del evento cuando inicien."
            />
          ) : null}

          {sinVideos ? (
            <RouteEmptyState
              icon={Clapperboard}
              title="Todavía no hay señales publicadas"
              description="Vuelve cuando empiecen los partidos o la transmisión principal del evento."
            />
          ) : null}

          {estado === "listo" && videos.length > 0 ? (
            <ol className="border-t border-border">
              {videos.map((video) => (
                <li key={video.id} className="border-b border-border">
                  <TarjetaPrograma video={video} />
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      </PortadaSection>
    </div>
  );
}
