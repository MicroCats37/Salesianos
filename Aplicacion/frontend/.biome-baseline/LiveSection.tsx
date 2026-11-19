"use client";

import { ArrowUpRight, CalendarPlus, Play } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ENLACES, FESTIVAL } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";

/**
 * Sección "06 / TRANSMISIÓN EN VIVO".
 *
 * El enlace oficial todavía no existe: la sección anuncia el canal y ofrece
 * guardar la fecha mientras tanto.
 */
export function LiveSection() {
  const [abierto, setAbierto] = useState(false);

  return (
    <PortadaSection
      id="en-vivo"
      eyebrow={COPY.enVivo.eyebrow}
      titulo={[...COPY.enVivo.titulo]}
      destacado={COPY.enVivo.destacado}
      copy={COPY.enVivo.copy}
    >
      <div className="mt-12 grid gap-10 lg:grid-cols-2 lg:items-center lg:gap-14">
        <div className="relative overflow-hidden rounded-2xl border border-[#312e8e]/10 shadow-xl shadow-[#312e8e]/10">
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
            className="absolute inset-0 bg-gradient-to-t from-[#17214b]/85 via-[#17214b]/25 to-transparent"
          />
          <span className="absolute top-4 left-4 inline-flex items-center gap-2 rounded-full bg-black/45 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-white backdrop-blur-sm">
            <span
              className="size-1.5 rounded-full bg-amber-400"
              aria-hidden="true"
            />
            {COPY.enVivo.estado}
          </span>
          <button
            type="button"
            onClick={() => setAbierto(true)}
            aria-label="Ver información de la transmisión"
            className="absolute inset-0 m-auto grid size-16 place-items-center rounded-full bg-white/90 text-[#312e8e] shadow-xl transition-transform hover:scale-105"
          >
            <Play className="size-7 fill-current" aria-hidden="true" />
          </button>
          <div className="absolute inset-x-0 bottom-0 p-5">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-sky-300">
              {FESTIVAL.nombre}
            </p>
            <p className="mt-1 text-sm font-bold uppercase tracking-wide text-white">
              EL FESTIVAL TAMBIÉN SE VIVE A DISTANCIA.
            </p>
          </div>
        </div>

        <div>
          <p className="text-sm leading-relaxed text-[#626195] sm:text-base">
            {COPY.enVivo.nota}
          </p>
          <button
            type="button"
            onClick={() => setAbierto(true)}
            className="mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
          >
            {COPY.enVivo.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent className="max-w-md text-center">
          <DialogTitle className="text-2xl font-black uppercase leading-tight tracking-tight text-[#17214b]">
            LA FAMILIA,
            <br />
            <span className="text-[#1557b8]">SIEMPRE CERCA.</span>
          </DialogTitle>
          <p className="mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-[#1557b8]">
            {COPY.enVivo.estado}
          </p>
          <p className="mt-4 text-sm leading-relaxed text-[#626195]">
            21 DE NOVIEMBRE DE 2026 · LIMA, PERÚ. La transmisión en vivo aún no
            está disponible: publicaremos el enlace oficial y los horarios para
            seguir el campeonato, las entrevistas y los momentos del festival.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <a
              href={ENLACES.calendario}
              download
              className="btn-brand-gradient btn-shine inline-flex h-12 w-full items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
            >
              <CalendarPlus className="size-4" aria-hidden="true" />
              GUARDAR LA FECHA
            </a>
            <a
              href={ENLACES.facebook}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
            >
              VER NOVEDADES
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
          </div>
        </DialogContent>
      </Dialog>
    </PortadaSection>
  );
}
