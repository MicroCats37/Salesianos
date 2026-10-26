"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CalendarPlus, ChevronDown, ExternalLink } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { ENLACES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";
import {
  CATEGORIAS_FALLBACK,
  useCategorias,
} from "@/features/portada/hooks/useCatalogo";

gsap.registerPlugin(ScrollTrigger);

/**
 * Publicación oficial del cronograma en Facebook.
 *
 * Enlace tomado del micrositio oficial (`index.html`, sección "programa").
 */
const CRONOGRAMA_FACEBOOK =
  "https://www.facebook.com/photo/?fbid=122118842211462108&set=pb.61593863260385.-2207520000";

/**
 * Sección "21 NOVIEMBRE / ORGANIZA TU DÍA".
 *
 * Timeline del día, acceso al cronograma oficial, descarga del calendario y
 * el desplegable con las categorías que expone el catálogo.
 */
export function ScheduleSection() {
  const rootRef = useRef<HTMLDivElement>(null);
  const { data: categorias } = useCategorias();

  const listaCategorias = useMemo(() => {
    const lista =
      categorias && categorias.length > 0 ? categorias : CATEGORIAS_FALLBACK;
    return [...lista].sort((a, b) => b.promocion_desde - a.promocion_desde);
  }, [categorias]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from("[data-hito]", {
        y: 28,
        opacity: 0,
        duration: 0.7,
        stagger: 0.08,
        ease: "power3.out",
        immediateRender: false,
        scrollTrigger: {
          trigger: root,
          start: "top 80%",
          once: true,
        },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  const destacado = COPY.programa.titulo.find((linea) =>
    linea.endsWith(COPY.programa.destacado),
  );

  return (
    <PortadaSection
      id="programa"
      eyebrow={COPY.programa.eyebrow}
      titulo={[...COPY.programa.titulo]}
      destacado={destacado}
    >
      <div ref={rootRef} className="mt-10">
        <div className="flex justify-end">
          <a
            href={CRONOGRAMA_FACEBOOK}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
          >
            {COPY.programa.enlaceCronograma}
            <ExternalLink className="size-4" aria-hidden="true" />
          </a>
        </div>

        <ol className="mt-10 flex flex-col lg:grid lg:grid-cols-5 lg:gap-6 lg:border-t-2 lg:border-[#22d3ee]/60">
          {COPY.programa.hitos.map((hito) => (
            <li
              key={`${hito.hora}-${hito.titulo}`}
              data-hito
              className="relative border-l-2 border-[#22d3ee]/35 pb-8 pl-6 last:pb-0 lg:border-l-0 lg:pb-0 lg:pt-8"
            >
              <span
                aria-hidden="true"
                className="absolute -left-[5px] top-1 size-3 rounded-full bg-[#22d3ee] shadow-[0_0_0_4px_rgba(34,211,238,0.18)] lg:-top-[7px] lg:left-0"
              />
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1557b8]">
                <time>{hito.hora}</time>{" "}
                <span className="text-[#626195]">{hito.meridiem}</span>
              </p>
              <h3 className="mt-2 text-lg font-black uppercase tracking-tight text-[#17214b]">
                {hito.titulo}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[#626195]">
                {hito.descripcion}
              </p>
            </li>
          ))}
        </ol>

        <div className="mt-10 flex flex-col gap-5 border-t border-[#312e8e]/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-[#626195]">{COPY.programa.notaPie}</p>
          <a
            href={ENLACES.calendario}
            download="Salesianos_FEST_2026.ics"
            className="btn-brand-gradient btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-sm font-black uppercase tracking-widest"
          >
            <CalendarPlus className="size-4" aria-hidden="true" />
            {COPY.programa.accionCalendario}
          </a>
        </div>

        <details className="group mt-10 rounded-2xl border border-[#312e8e]/12 bg-white/70 p-5 sm:p-6">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-black uppercase tracking-wider text-[#17214b]">
            {COPY.programa.categorias.titulo}
            <ChevronDown
              className="size-5 shrink-0 transition-transform group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {listaCategorias.map((categoria) => (
              <div key={categoria.id} className="card-elevated rounded-2xl p-5">
                <h3 className="text-base font-black uppercase tracking-tight text-[#17214b]">
                  {categoria.nombre}
                </h3>
                <p className="mt-2 text-sm text-[#626195]">
                  Promociones {categoria.promocion_desde}–
                  {categoria.promocion_hasta}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-xs leading-relaxed text-[#626195]">
            {COPY.programa.categorias.nota}
          </p>
        </details>
      </div>
    </PortadaSection>
  );
}
