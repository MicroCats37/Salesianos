import { ArrowLeft, Clapperboard } from "lucide-react";
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
import type { EstadoVistaVideos, Video } from "../types/video.types";

export interface VideoDetalleViewProps {
  /** The state of the read. */
  estado?: EstadoVistaVideos;
  /** The video, when the server published it. */
  video?: Video;
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
 * The day a video was published.
 *
 * The date is formatted in UTC with an explicit calendar: the server and the
 * browser must say the SAME day, or the page would change under the visitor
 * when it hydrates.
 */
function fechaPublicada(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";

  const meses = [
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

  return `${fecha.getUTCDate()} de ${meses[fecha.getUTCMonth()]} de ${fecha.getUTCFullYear()}`;
}

/**
 * VID-02 - the detail of a video.
 *
 * The stage is the centre of the page: the video opens HERE, on the same
 * surface that announced it, and the description travels below it in the
 * measure of a reading.
 *
 * The player never invents a source: it plays the address that the server
 * published, or it offers to open it outside.
 */
export function VideoDetalleView({
  estado = "sin-datos",
  video,
  mensajeError,
  reintentar,
}: VideoDetalleViewProps) {
  const publicado = video ? fechaPublicada(video.created_at) : "";

  return (
    <div className="relative left-1/2 -mx-4 -my-10 w-screen -translate-x-1/2 sm:-mx-6 sm:-my-12 lg:-mx-10">
      <PortadaSection
        fondo="pagina"
        altura="auto"
      >
        <div className="flex flex-col gap-6">
          <Link
            href={RUTAS.publico.videos}
            className="inline-flex w-fit min-h-11 items-center gap-2 rounded-full border border-brand-on-gradient-border px-4 text-sm font-semibold text-brand-on-gradient transition-colors hover:bg-brand-on-gradient/10"
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            Ver todas las transmisiones
          </Link>

          {estado === "sin-permiso" ? (
            <ShellPermissionDenied
              title="No podemos mostrar esta transmisión"
              description="Esta señal no está disponible para ti ahora mismo."
              className="border-border bg-surface-raised"
            />
          ) : null}

          {estado === "cargando" ? (
            <ShellPendingState
              title="Preparando la transmisión"
              description="Estamos conectando con la señal publicada."
            />
          ) : null}

          {estado === "error" ? (
            <ShellErrorState
              title="No pudimos cargar esta transmisión"
              description={
                mensajeError ??
                "No pudimos conectar con esta señal en este momento. Vuelve a intentarlo en unos segundos."
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
              title="Este video todavía no está disponible"
              description="El servicio de contenido publica la galería. Cuando el video exista, esta pantalla lo abrirá aquí."
            />
          ) : null}

          {estado === "listo" && video ? (
            <div className="flex flex-col gap-6">
              <div className="mx-auto flex w-full max-w-[70rem] flex-col gap-3">
                <PatrocinadoresVideoBanner />
                <div className="relative overflow-hidden rounded-[var(--radius-2xl)] border border-border bg-surface-inverse shadow-[var(--elevation-lg)]">
                  <div className="aspect-video w-full">
                    <ReproductorVideo url={video.url} titulo={video.titulo} />
                  </div>
                  <div className="pointer-events-none absolute left-4 top-4 rounded-[var(--radius-md)] border border-brand-on-gradient-border bg-surface-inverse/90 px-3 py-2 backdrop-blur-sm sm:left-6 sm:top-6">
                    <p className="text-caption font-semibold text-brand-cyan">
                      SEÑAL OFICIAL / EN VIVO
                    </p>
                    <h1 className="mt-1 max-w-[18rem] text-lg font-black leading-tight text-brand-on-gradient sm:text-xl">
                      {video.titulo}
                    </h1>
                  </div>
                </div>
                <PatrocinadoresVideoBanner invertido />
              </div>

              <div className="mx-auto flex w-full max-w-[70rem] flex-col gap-2">
                {video.descripcion ? (
                  <p className="max-w-reading text-sm text-muted-foreground sm:text-base">
                    {video.descripcion}
                  </p>
                ) : null}
                {publicado ? (
                  <p className="text-caption text-muted-foreground">
                    Publicado el {publicado}
                  </p>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </PortadaSection>
    </div>
  );
}
