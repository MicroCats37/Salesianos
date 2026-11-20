import { Clapperboard } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import {
  ShellErrorState,
  ShellPendingState,
  ShellPermissionDenied,
} from "@/components/shell/ShellState";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { TarjetaVideo } from "../components/TarjetaVideo";
import type { EstadoVistaVideos, VideoListItem } from "../types/video.types";

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
 * The reveal of the wall of screens.
 *
 * It is OPT-IN and it uses the token of the brand (`--animate-fade-up`): the
 * gallery opens like a room whose lights come on one screen at a time. The
 * motion is reduced to nothing when the visitor asked for it.
 */
const REVELAR = {
  animation: "var(--animate-fade-up)",
  animationFillMode: "both",
} as const;

/**
 * VID-01 - the public gallery of videos.
 *
 * The gallery is a PLACE, not a list: the visitor arrives at the room where
 * the festival is projected and chooses the screen that he wants to open.
 *
 * The grid waits for the server: it never fills itself with example videos,
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
    <div className="relative left-1/2 -mx-4 -my-10 w-screen -translate-x-1/2 sm:-mx-6 sm:-my-12 lg:-mx-10">
      <PortadaSection
        id="transmisiones"
        eyebrow="EN VIVO / SALESIANOS FEST"
        titulo={["PARTIDOS.", "EVENTO.", "EN VIVO."]}
        destacado="EN VIVO."
        copy="Sigue las señales oficiales del campeonato y los momentos centrales del festival."
        fondo="pagina"
        contenidoClassName="py-4"
      >
        <div className="mt-10">
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
            <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {videos.map((video, indice) => (
                <li
                  key={video.id}
                  className="motion-reduce:[animation:none]"
                  style={{
                    ...REVELAR,
                    animationDelay: `${indice * 70}ms`,
                  }}
                >
                  <TarjetaVideo video={video} />
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </PortadaSection>
    </div>
  );
}
