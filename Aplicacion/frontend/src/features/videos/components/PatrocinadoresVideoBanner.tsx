"use client";

import { usePatrocinadoresPublicos } from "@/features/patrocinadores/hooks/usePatrocinadores";
import { cn, resolveImageUrl } from "@/lib/utils";

export interface PatrocinadoresVideoBannerProps {
  invertido?: boolean;
  orientacion?: "horizontal" | "vertical";
  transparente?: boolean;
  className?: string;
}

function externalUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:"
      ? url.href
      : null;
  } catch {
    return null;
  }
}

/** Infinite sponsor rail framing the public live broadcast. */
export function PatrocinadoresVideoBanner({
  invertido = false,
  orientacion = "horizontal",
  transparente = false,
  className,
}: PatrocinadoresVideoBannerProps) {
  const consulta = usePatrocinadoresPublicos();
  const patrocinadores = (consulta.data ?? []).flatMap((patrocinador) => {
    if (!patrocinador.visible) return [];

    const imagen = patrocinador.imagenes.find(
      (item) => item.url && item.disponible,
    );
    const medio =
      patrocinador.logo?.url && patrocinador.logo.disponible
        ? patrocinador.logo.url
        : imagen?.url;

    return medio ? [{ patrocinador, medio }] : [];
  });

  if (consulta.isPending || patrocinadores.length === 0) return null;

  const esVertical = orientacion === "vertical";
  const cantidadRepeticiones = Math.max(
    1,
    Math.ceil((esVertical ? 8 : 6) / patrocinadores.length),
  );
  const base = Array.from(
    { length: cantidadRepeticiones },
    () => patrocinadores,
  ).flat();
  const pista = [...base, ...base];

  return (
    <aside
      aria-label="Patrocinadores de esta transmisión"
      className={cn(
        "overflow-hidden py-1",
        transparente
          ? ""
          : "rounded-[var(--radius-xl)] border border-brand-on-gradient-border bg-brand-gradient-deep",
        esVertical && "min-h-[22rem]",
        className,
      )}
    >
      <div
        className={cn(
          "flex gap-8 hover:[animation-play-state:paused] motion-reduce:animate-none",
          esVertical
            ? "h-max flex-col px-3 animate-[var(--animate-marquee-vertical)]"
            : "w-max px-3 animate-[var(--animate-marquee)]",
          invertido && "[animation-direction:reverse]",
        )}
      >
        {pista.map(({ patrocinador, medio }, indice) => {
          const sitioWeb = externalUrl(patrocinador.sitio_web);
          const logo = (
            <img
              src={resolveImageUrl(medio)}
              alt={patrocinador.nombre}
              className={cn(
                "object-contain opacity-90 transition-opacity hover:opacity-100",
                esVertical ? "h-12 max-w-28" : "h-16 max-w-48",
              )}
            />
          );

          return (
            <div
              key={`${patrocinador.id}-${indice}`}
              className="flex shrink-0 items-center justify-center"
            >
              {sitioWeb ? (
                <a
                  href={sitioWeb}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-cyan"
                >
                  {logo}
                  <span className="sr-only">
                    Visitar el sitio web de {patrocinador.nombre} (abre en una
                    nueva pestaña)
                  </span>
                </a>
              ) : (
                logo
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
