"use client";

import { ArrowUpRight, Share2 } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import {
  type PromotionDialogMode,
  SharePromotionDialog,
} from "@/components/portada/SharePromotionDialog";
import { ENLACES, SECCIONES } from "@/features/portada/config/festival";
import {
  PROMOCIONES,
  type Promocion,
} from "@/features/portada/config/promotions";
import { COPY } from "@/features/portada/copy";

interface Seleccion {
  promocion: Promocion;
  modo: PromotionDialogMode;
}

/**
 * Sección "LA FAMILIA SIGUE CRECIENDO".
 *
 * Rejilla de las promociones confirmadas (carrusel con scroll-snap en
 * móvil) más la tarjeta de invitación. Cada afiche abre el diálogo con el
 * anuncio oficial y las vías de compartir.
 */
export function PromotionsSection() {
  const [seleccion, setSeleccion] = useState<Seleccion | null>(null);

  const abrir = (promocion: Promocion, modo: PromotionDialogMode) => {
    setSeleccion({ promocion, modo });
  };

  return (
    <PortadaSection
      id={SECCIONES.promociones}
      eyebrow={COPY.promociones.eyebrow}
      titulo={[...COPY.promociones.titulo]}
      destacado={COPY.promociones.destacado}
      copy={[...COPY.promociones.copy]}
    >
      <div className="-mx-4 mt-12 grid snap-x snap-mandatory grid-flow-col auto-cols-[78%] gap-4 overflow-x-auto px-4 pb-6 sm:-mx-6 sm:px-6 md:mx-0 md:grid-flow-row md:auto-cols-auto md:grid-cols-2 md:overflow-visible md:px-0 md:pb-0 md:snap-none lg:grid-cols-4">
        {PROMOCIONES.map((promocion) => (
          <article
            key={promocion.anio}
            data-portada-stagger
            className="card-elevated card-elevated-hover flex snap-start flex-col overflow-hidden rounded-2xl"
          >
            <button
              type="button"
              onClick={() => abrir(promocion, "poster")}
              aria-label={COPY.promociones.share.verAnuncio.replace(
                "{anio}",
                String(promocion.anio),
              )}
              className="group relative block w-full text-left"
            >
              <div className="relative aspect-[4/5] w-full overflow-hidden bg-[#312e8e]/5">
                <Image
                  src={promocion.imagen}
                  alt={COPY.promociones.share.altPoster.replace(
                    "{anio}",
                    String(promocion.anio),
                  )}
                  fill
                  loading="lazy"
                  sizes="(min-width: 1024px) 25vw, (min-width: 768px) 50vw, 78vw"
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                />
              </div>
              <span className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 bg-gradient-to-t from-[#17214b]/95 via-[#17214b]/70 to-transparent p-4">
                <span>
                  <span className="block text-[9px] font-black uppercase tracking-[0.2em] text-white/70">
                    {COPY.promociones.etiqueta}
                  </span>
                  <span className="block text-2xl font-black leading-none text-white">
                    {promocion.anio}
                  </span>
                </span>
                <span className="text-[9px] font-black uppercase tracking-[0.14em] text-[#22d3ee]">
                  {COPY.promociones.estado} ↗
                </span>
              </span>
            </button>

            <button
              type="button"
              onClick={() => abrir(promocion, "compartir")}
              aria-label={COPY.promociones.share.compartirAnuncio.replace(
                "{anio}",
                String(promocion.anio),
              )}
              className="mt-auto flex min-h-12 items-center gap-2 border-t border-[#312e8e]/10 px-4 py-3 text-[11px] font-black uppercase tracking-wider text-[#1557b8] transition-colors hover:bg-[#1557b8]/8"
            >
              <Share2 className="size-4" aria-hidden="true" />
              {COPY.promociones.accionCompartir}
            </button>
          </article>
        ))}

        <div
          data-portada-stagger
          className="flex snap-start flex-col rounded-2xl border border-dashed border-[#312e8e]/30 bg-[#312e8e]/[0.04] p-5 sm:p-6"
        >
          <span aria-hidden="true" className="text-3xl text-[#22d3ee]">
            ✦
          </span>
          <p className="mt-3 text-[10px] font-black uppercase tracking-[0.2em] text-[#1557b8]">
            {COPY.promociones.invitacion.miniLabel}
          </p>
          <h3 className="mt-2 text-xl font-black uppercase leading-[1.05] tracking-tight text-[#17214b]">
            {COPY.promociones.invitacion.titulo.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {linea}
              </span>
            ))}
          </h3>
          <p className="mt-3 text-sm leading-relaxed text-[#626195]">
            {COPY.promociones.invitacion.descripcion}
          </p>
          <a
            href={`#${SECCIONES.paquetes}`}
            className="btn-brand-gradient btn-shine mt-6 inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-widest"
          >
            {COPY.promociones.invitacion.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </div>
      </div>

      <div
        data-portada-stagger
        className="mt-10 flex flex-col gap-4 border-t border-[#312e8e]/15 pt-6 sm:flex-row sm:items-center sm:justify-between"
      >
        <p className="max-w-2xl text-xs leading-relaxed text-[#626195]">
          {COPY.promociones.pie.aviso}
        </p>
        <a
          href={ENLACES.facebook}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
        >
          {COPY.promociones.pie.enlace}
          <ArrowUpRight className="size-4" aria-hidden="true" />
        </a>
      </div>

      <SharePromotionDialog
        promocion={seleccion?.promocion ?? null}
        modo={seleccion?.modo ?? "poster"}
        open={Boolean(seleccion)}
        onOpenChange={(open) => {
          if (!open) setSeleccion(null);
        }}
      />
    </PortadaSection>
  );
}
