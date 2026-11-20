"use client";

import { usePatrocinadoresPublicos } from "@/features/patrocinadores/hooks/usePatrocinadores";
import { resolveImageUrl } from "@/lib/utils";

export interface PatrocinadoresVideoBannerProps {
  invertido?: boolean;
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

  const cantidadRepeticiones = Math.max(1, Math.ceil(6 / patrocinadores.length));
  const base = Array.from(
    { length: cantidadRepeticiones },
    () => patrocinadores,
  ).flat();
  const pista = [...base, ...base];

  return (
    <aside
      aria-label="Patrocinadores de esta transmisión"
      className="overflow-hidden rounded-[var(--radius-xl)] border border-brand-on-gradient-border bg-brand-gradient-deep py-3 shadow-[var(--elevation-sm)]"
    >
      <div
        className={`flex w-max gap-3 px-3 animate-[var(--animate-marquee)] hover:[animation-play-state:paused] motion-reduce:animate-none ${
          invertido ? "[animation-direction:reverse]" : ""
        }`}
      >
        {pista.map(({ patrocinador, medio }, indice) => {
          const sitioWeb = externalUrl(patrocinador.sitio_web);
          const contenido = (
            <>
              <img
                src={resolveImageUrl(medio)}
                alt={patrocinador.nombre}
                className="h-14 max-w-32 object-contain"
              />
              <span className="max-w-24 truncate text-caption font-semibold text-foreground">
                {patrocinador.nombre}
              </span>
            </>
          );

          return (
            <div
              key={`${patrocinador.id}-${indice}`}
              className="flex w-44 shrink-0 items-center justify-center"
            >
              {sitioWeb ? (
                <a
                  href={sitioWeb}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex w-full flex-col items-center justify-center gap-1 rounded-[var(--radius-lg)] bg-background px-3 py-2 transition-transform hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {contenido}
                  <span className="sr-only">
                    Visitar el sitio web de {patrocinador.nombre} (abre en una
                    nueva pestaña)
                  </span>
                </a>
              ) : (
                <div className="flex w-full flex-col items-center justify-center gap-1 rounded-[var(--radius-lg)] bg-background px-3 py-2">
                  {contenido}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
