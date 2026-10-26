"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import {
  type KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { SECCIONES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";
import {
  DISCIPLINAS_FALLBACK,
  ORDEN_DISCIPLINAS,
  presentacionDisciplina,
  useDisciplinas,
} from "@/features/portada/hooks/useCatalogo";
import { cn } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

/**
 * Sección "02 / EL CAMPEONATO".
 *
 * Cuatro tabs (una por disciplina) alimentan un panel accesible y la figura
 * lateral: título, detalle, imagen, stat de canchas y fecha del torneo.
 */
export function ChampionshipSection() {
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const botonesRef = useRef<(HTMLButtonElement | null)[]>([]);
  const [siglaActiva, setSiglaActiva] = useState<string>("F7M");
  const { data: disciplinas } = useDisciplinas();

  const tabs = useMemo(() => {
    const lista =
      disciplinas && disciplinas.length > 0
        ? disciplinas
        : DISCIPLINAS_FALLBACK;
    return [...lista].sort((a, b) => {
      const posicionA = ORDEN_DISCIPLINAS.indexOf(
        a.sigla as (typeof ORDEN_DISCIPLINAS)[number],
      );
      const posicionB = ORDEN_DISCIPLINAS.indexOf(
        b.sigla as (typeof ORDEN_DISCIPLINAS)[number],
      );
      if (posicionA === posicionB)
        return a.nombre.localeCompare(b.nombre, "es");
      if (posicionA === -1) return 1;
      if (posicionB === -1) return -1;
      return posicionA - posicionB;
    });
  }, [disciplinas]);

  const activa =
    tabs.find((tabla) => tabla.sigla === siglaActiva) ??
    tabs[0] ??
    DISCIPLINAS_FALLBACK[0];
  const siglaSeleccionada = activa.sigla;
  const presentacion = presentacionDisciplina(activa.sigla, activa.nombre);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from("[data-campeonato-visual]", {
        y: 40,
        opacity: 0,
        duration: 0.9,
        ease: "power3.out",
        immediateRender: false,
        scrollTrigger: {
          trigger: root,
          start: "top 78%",
          once: true,
        },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  useEffect(() => {
    const panel = panelRef.current;
    if (!panel || !siglaSeleccionada) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        panel,
        { opacity: 0, x: 20 },
        {
          opacity: 1,
          x: 0,
          duration: 0.35,
          ease: "power2.out",
          overwrite: true,
        },
      );
    }, panel);
    return () => ctx.revert();
  }, [siglaSeleccionada]);

  const moverConFlechas = (
    evento: KeyboardEvent<HTMLButtonElement>,
    indice: number,
  ) => {
    let destino: number | undefined;
    if (evento.key === "ArrowRight") destino = (indice + 1) % tabs.length;
    if (evento.key === "ArrowLeft")
      destino = (indice - 1 + tabs.length) % tabs.length;
    if (evento.key === "Home") destino = 0;
    if (evento.key === "End") destino = tabs.length - 1;
    if (destino === undefined) return;

    evento.preventDefault();
    const tabla = tabs[destino];
    setSiglaActiva(tabla.sigla);
    botonesRef.current[destino]?.focus();
  };

  const destacado = COPY.campeonato.titulo.find((linea) =>
    linea.endsWith(COPY.campeonato.destacado),
  );

  return (
    <PortadaSection
      id="campeonato"
      eyebrow={COPY.campeonato.eyebrow}
      titulo={[...COPY.campeonato.titulo]}
      destacado={destacado}
      copy={COPY.campeonato.copy}
    >
      <div ref={rootRef} className="mt-12">
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-14">
          <div>
            <div
              role="tablist"
              aria-label="Disciplinas deportivas"
              className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0 lg:flex-wrap lg:overflow-visible"
            >
              {tabs.map((tabla, indice) => {
                const seleccionado = tabla.sigla === siglaSeleccionada;
                return (
                  <button
                    key={tabla.sigla}
                    type="button"
                    role="tab"
                    id={`tab-${tabla.sigla}`}
                    aria-selected={seleccionado}
                    aria-controls="panel-disciplina"
                    tabIndex={seleccionado ? 0 : -1}
                    ref={(elemento) => {
                      botonesRef.current[indice] = elemento;
                    }}
                    onClick={() => setSiglaActiva(tabla.sigla)}
                    onKeyDown={(evento) => moverConFlechas(evento, indice)}
                    className={cn(
                      "h-12 shrink-0 whitespace-nowrap rounded-full px-5 text-xs font-black uppercase tracking-wider transition-colors",
                      seleccionado
                        ? "bg-[#312e8e] text-white shadow-lg shadow-[#312e8e]/20"
                        : "border border-[#312e8e]/20 bg-white/70 text-[#312e8e] hover:bg-[#312e8e]/5",
                    )}
                  >
                    {tabla.nombre}
                  </button>
                );
              })}
            </div>

            <div
              id="panel-disciplina"
              role="tabpanel"
              aria-labelledby={`tab-${siglaSeleccionada}`}
              ref={panelRef}
              className="card-elevated mt-8 rounded-2xl p-5 sm:p-6"
            >
              <h3 className="text-xl font-black uppercase tracking-tight text-[#17214b] sm:text-2xl">
                {activa.nombre}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#626195] sm:text-base">
                {presentacion.canchas} Equipos con un mínimo de{" "}
                {activa.min_jugadores} integrantes.
              </p>
              <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2">
                <span className="rounded-full bg-[#312e8e] px-4 py-2 text-[11px] font-black uppercase tracking-[0.2em] text-white">
                  {presentacion.stat}
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#626195]">
                  {presentacion.etiqueta}
                </span>
              </div>
            </div>

            <a
              href={`#${SECCIONES.paquetes}`}
              className="mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
            >
              {COPY.campeonato.enlace}
              <ArrowRight className="size-4" aria-hidden="true" />
            </a>
          </div>

          <div className="lg:sticky lg:top-24 lg:self-start">
            <div
              data-campeonato-visual
              className="relative overflow-hidden rounded-2xl border border-[#312e8e]/10 shadow-xl shadow-[#312e8e]/10"
            >
              <div className="relative aspect-[4/3] w-full">
                <Image
                  src={presentacion.imagen}
                  alt={presentacion.alt}
                  fill
                  loading="lazy"
                  sizes="(max-width: 1024px) 100vw, 50vw"
                  className="object-cover"
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-4 bg-gradient-to-t from-[#17214b]/90 via-[#17214b]/45 to-transparent p-5">
                <div aria-hidden="true">
                  <span className="block text-xl font-black uppercase tracking-wider text-white">
                    {presentacion.stat}
                  </span>
                  <small className="mt-1 block text-[10px] font-black uppercase tracking-[0.2em] text-[#22d3ee]">
                    {presentacion.etiqueta}
                  </small>
                </div>
                <div className="rounded-xl bg-white/95 px-4 py-2 text-center">
                  <b className="block text-2xl font-black leading-none text-[#312e8e]">
                    {COPY.campeonato.fecha.dia}
                  </b>
                  <span className="mt-1 block text-[9px] font-black uppercase tracking-[0.2em] text-[#626195]">
                    {COPY.campeonato.fecha.mes}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap gap-3 border-t border-[#312e8e]/10 pt-8">
          {COPY.campeonato.perks.map((perk) => (
            <span
              key={perk}
              className="rounded-full border border-[#312e8e]/15 bg-white/70 px-4 py-2 text-[11px] font-black uppercase tracking-wider text-[#312e8e]"
            >
              {perk}
            </span>
          ))}
        </div>
      </div>
    </PortadaSection>
  );
}
