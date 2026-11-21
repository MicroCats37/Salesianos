"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CalendarPlus, ChevronDown, ExternalLink } from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useRef } from "react";
import { useCatalogoCategorias } from "@/features/inscripciones/hooks/useCatalogo";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES } from "@/features/portada/fixtures/festival";

gsap.registerPlugin(ScrollTrigger);

/**
 * Publicación oficial del cronograma en Facebook.
 *
 * Enlace tomado del micrositio oficial (`index.html`, sección "programa").
 */
const CRONOGRAMA_FACEBOOK =
  "https://www.facebook.com/photo/?fbid=122118842211462108&set=pb.61593863260385.-2207520000";

/**
 * Los carteles oficiales de la jornada.
 *
 * Son la cartelera gráfica de la sección: cada bloque del día —las tres
 * disciplinas y la fiesta— tiene su propio cartel, y cada uno abre la parte
 * de la página donde ese bloque se cuenta.
 */
const CARTELERA = [
  {
    src: "/images/section/Tarjeta_Voley_960x540.webp",
    alt: "Cartel del campeonato de vóley mixto interpromociones del Salesianos Fest",
    href: "#campeonato",
  },
  {
    src: "/images/section/Tarjeta_Fulbito_960x540.webp",
    alt: "Cartel del campeonato de fúlbito interpromociones del Salesianos Fest",
    href: "#campeonato",
  },
  {
    src: "/images/section/Tarjeta_Basquet_960x540.webp",
    alt: "Cartel del campeonato de básquet interpromociones del Salesianos Fest",
    href: "#campeonato",
  },
  {
    src: "/images/section/Tarjeta_Fiesta_960x540.webp",
    alt: "Cartel de la fiesta en el auditorio de la Asociación Okinawense del Perú",
    href: "#fiesta",
  },
];

/**
 * Sección "21 NOVIEMBRE / ORGANIZA TU DÍA".
 *
 * Timeline del día, acceso al cronograma oficial, descarga del calendario y
 * el desplegable con las categorías que expone el catálogo.
 *
 * ## Las categorías son una LECTURA REAL
 *
 * La sección ya no pinta un fixture: las categorías del desplegable son las
 * que publica el catálogo de la edición, leídas por el ÚNICO cliente del
 * catálogo (`useCatalogoCategorias`). Cuando el servidor no publica
 * categorías —o no se puede leer el catálogo— la sección lo dice, y no
 * inventa cuatro bandas que ningún backend declara.
 */
export function ScheduleSection() {
  const rootRef = useRef<HTMLDivElement>(null);
  const categorias = useCatalogoCategorias();

  const listaCategorias = useMemo(() => {
    const lista = categorias.data?.categorias ?? [];
    return [...lista].sort((a, b) => b.promocion_desde - a.promocion_desde);
  }, [categorias.data]);

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
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {CARTELERA.map((cartel) => (
            <li key={cartel.src}>
              <a
                href={cartel.href}
                className="group block overflow-hidden rounded-[var(--radius-xl)] border border-border shadow-[var(--elevation-sm)] transition-[transform,box-shadow] duration-(--motion-duration-base) hover:-translate-y-1 hover:shadow-[var(--elevation-md)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                <Image
                  src={cartel.src}
                  alt={cartel.alt}
                  width={960}
                  height={540}
                  loading="lazy"
                  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                  className="h-auto w-full"
                />
              </a>
            </li>
          ))}
        </ul>

        <div className="mt-10 flex justify-end">
          <a
            href={CRONOGRAMA_FACEBOOK}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
          >
            {COPY.programa.enlaceCronograma}
            <ExternalLink className="size-4" aria-hidden="true" />
          </a>
        </div>

        <ol className="mt-10 flex flex-col lg:grid lg:grid-cols-5 lg:gap-6 lg:border-t-2 lg:border-brand-cyan/60">
          {COPY.programa.hitos.map((hito) => (
            <li
              key={`${hito.hora}-${hito.titulo}`}
              data-hito
              className="relative border-l-2 border-brand-cyan/35 pb-8 pl-6 last:pb-0 lg:border-l-0 lg:pb-0 lg:pt-8"
            >
              <span
                aria-hidden="true"
                className="absolute -left-[5px] top-1 size-3 rounded-full bg-brand-cyan shadow-[0_0_0_4px_color-mix(in_srgb,var(--brand-cyan)_18%,transparent)] lg:-top-[7px] lg:left-0"
              />
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-info">
                <time>{hito.hora}</time>{" "}
                <span className="text-muted-foreground">{hito.meridiem}</span>
              </p>
              <h3 className="mt-2 text-lg font-black uppercase tracking-tight text-foreground">
                {hito.titulo}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {hito.descripcion}
              </p>
            </li>
          ))}
        </ol>

        <div className="mt-10 flex flex-col gap-5 border-t border-primary/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {COPY.programa.notaPie}
          </p>
          <a
            href={ENLACES.calendario}
            download="Salesianos_FEST_2026.ics"
            className="btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full bg-accent px-6 text-sm font-black uppercase tracking-widest text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
          >
            <CalendarPlus className="size-4" aria-hidden="true" />
            {COPY.programa.accionCalendario}
          </a>
        </div>

        <details className="group mt-10 rounded-2xl border border-primary/12 bg-surface-raised/70 p-5 sm:p-6">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-black uppercase tracking-wider text-foreground">
            {COPY.programa.categorias.titulo}
            <ChevronDown
              className="size-5 shrink-0 transition-transform group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {listaCategorias.map((categoria) => (
              <div key={categoria.id} className="card-elevated rounded-2xl p-5">
                <h3 className="text-base font-black uppercase tracking-tight text-foreground">
                  {categoria.nombre}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Promociones {categoria.promocion_desde}–
                  {categoria.promocion_hasta}
                </p>
              </div>
            ))}
          </div>
          {listaCategorias.length === 0 ? (
            <p className="mt-6 text-sm text-muted-foreground">
              {categorias.isError
                ? "No pudimos leer las categorías de la edición. Vuelve a intentarlo en unos segundos."
                : "Las categorías de la edición se publican cuando el comité las declara."}
            </p>
          ) : null}
          <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
            {COPY.programa.categorias.nota}
          </p>
        </details>
      </div>
    </PortadaSection>
  );
}
