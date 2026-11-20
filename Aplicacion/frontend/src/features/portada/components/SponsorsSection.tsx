"use client";

"use client";

import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Pause,
  Play,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES } from "@/features/portada/fixtures/festival";
import { usePatrocinadoresPublicos } from "@/features/patrocinadores/hooks/usePatrocinadores";
import { useGSAP } from "@/hooks/system/use-gsap";
import { resolveImageUrl } from "@/lib/utils";

const BENEFICIOS = [
  "Presencia de marca en el espacio de auspiciadores de la web.",
  "Posibles activaciones durante el festival.",
  "Opciones de colaboración vinculadas al deporte, la familia y la fiesta.",
];

/**
 * Sección "08 / AUSPICIADORES Y ALIADOS".
 *
 * La lista de auspiciadores la confirma la organización: mientras está
 * vacía solo se muestra la invitación (nunca un grid vacío).
 */
export function SponsorsSection() {
  const [abierto, setAbierto] = useState(false);
  const [indice, setIndice] = useState(0);
  const [pausado, setPausado] = useState(false);
  const [movimientoReducido, setMovimientoReducido] = useState(false);
  const carruselRef = useRef<HTMLDivElement>(null);
  const patrocinadores = usePatrocinadoresPublicos();
  const activos = (patrocinadores.data ?? []).filter((patrocinador) => patrocinador.visible);
  const total = activos.length;
  const actual = activos[indice] ?? activos[0];

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const actualizar = () => setMovimientoReducido(media.matches);
    actualizar();
    media.addEventListener("change", actualizar);
    return () => media.removeEventListener("change", actualizar);
  }, []);

  useEffect(() => {
    if (total === 0 && indice !== 0) setIndice(0);
    if (indice >= total && total > 0) setIndice(total - 1);
  }, [indice, total]);

  useEffect(() => {
    if (total < 2 || pausado || movimientoReducido) return;
    const interval = window.setInterval(
      () => setIndice((actualIndice) => (actualIndice + 1) % total),
      6000,
    );
    return () => window.clearInterval(interval);
  }, [movimientoReducido, pausado, total]);

  useGSAP(
    () => {
      if (movimientoReducido) return;
      const slide = carruselRef.current?.querySelector("[data-sponsor-slide]");
      if (slide) {
        gsap.fromTo(
          slide,
          { autoAlpha: 0, y: 18 },
          { autoAlpha: 1, y: 0, duration: 0.48, ease: "power2.out" },
        );
      }
    },
    { scope: carruselRef, dependencies: [indice, movimientoReducido] },
  );

  const irA = (proximo: number) => {
    if (total > 0) setIndice((proximo + total) % total);
  };

  return (
    <PortadaSection
      id="auspiciadores"
      eyebrow={COPY.auspiciadores.eyebrow}
      titulo={[...COPY.auspiciadores.titulo]}
      destacado={COPY.auspiciadores.destacado}
      copy={COPY.auspiciadores.copy}
    >
      {actual ? (
        <div
          ref={carruselRef}
          role="region"
          aria-roledescription="carrusel"
          aria-label="Patrocinadores del festival"
          tabIndex={0}
          onKeyDown={(evento) => {
            if (evento.key === "ArrowLeft") irA(indice - 1);
            if (evento.key === "ArrowRight") irA(indice + 1);
            if (evento.key === "Home") irA(0);
            if (evento.key === "End") irA(total - 1);
          }}
          className="mt-12 rounded-[var(--radius-xl)] bg-brand-gradient-deep p-1 shadow-xl shadow-primary/20 outline-none focus-visible:ring-4 focus-visible:ring-ring/50"
        >
          <article data-sponsor-slide className="grid overflow-hidden rounded-[calc(var(--radius-xl)-4px)] bg-brand-deep-navy sm:grid-cols-[1.1fr_0.9fr]">
            <div className="relative min-h-64 overflow-hidden bg-brand-deep-night sm:min-h-80">
              {actual.imagenes[0]?.url && actual.imagenes[0].disponible ? (
                <img src={resolveImageUrl(actual.imagenes[0].url)} alt={actual.imagenes[0].texto_alternativo || actual.nombre} className="size-full absolute inset-0 object-cover opacity-75" />
              ) : null}
              <div aria-hidden="true" className="absolute inset-0 bg-gradient-to-tr from-brand-deep-night via-brand-deep-navy/75 to-transparent" />
              <div className="relative flex size-full min-h-64 items-end p-6 sm:min-h-80 sm:p-8">
                <span className="max-w-[13rem] rounded-[var(--radius-md)] bg-surface-raised/95 p-4 shadow-lg backdrop-blur-sm">
                  {actual.logo?.url && actual.logo.disponible ? <img src={resolveImageUrl(actual.logo.url)} alt={`Logo de ${actual.nombre}`} className="max-h-16 max-w-full object-contain" /> : <span className="font-heading text-xl font-black uppercase tracking-tight text-foreground">{actual.nombre}</span>}
                </span>
              </div>
            </div>
            <div className="flex flex-col justify-between gap-8 p-6 text-brand-on-gradient sm:p-8">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.28em] text-accent">Aliado del festival</p>
                <h3 className="mt-3 font-heading text-3xl font-black leading-none tracking-tight sm:text-4xl">{actual.nombre}</h3>
                {actual.descripcion ? <p className="mt-4 max-w-md text-sm leading-relaxed text-brand-on-gradient/75">{actual.descripcion}</p> : null}
                {actual.sitio_web ? <a href={actual.sitio_web} target="_blank" rel="noopener noreferrer" className="mt-5 inline-flex text-sm font-bold text-accent underline underline-offset-4 hover:text-accent-muted">Conocer a {actual.nombre}<span className="sr-only"> (abre en una nueva pestaña)</span></a> : null}
              </div>
              <div className="flex items-center justify-between gap-4">
                <div className="flex gap-2" aria-label={`Patrocinador ${indice + 1} de ${total}`}>
                  {activos.map((patrocinador, posicion) => <button key={patrocinador.id} type="button" onClick={() => irA(posicion)} aria-label={`Mostrar patrocinador ${posicion + 1}: ${patrocinador.nombre}`} aria-current={posicion === indice} className="grid size-10 place-items-center rounded-full border border-brand-on-gradient/25 text-xs font-bold transition-colors hover:bg-brand-on-gradient/15 aria-[current=true]:border-accent aria-[current=true]:bg-accent aria-[current=true]:text-accent-foreground">{posicion + 1}</button>)}
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={() => irA(indice - 1)} className="grid size-11 place-items-center rounded-full border border-brand-on-gradient/25 hover:bg-brand-on-gradient/15" aria-label="Patrocinador anterior"><ChevronLeft className="size-5" aria-hidden="true" /></button>
                  <button type="button" onClick={() => irA(indice + 1)} className="grid size-11 place-items-center rounded-full border border-brand-on-gradient/25 hover:bg-brand-on-gradient/15" aria-label="Patrocinador siguiente"><ChevronRight className="size-5" aria-hidden="true" /></button>
                  <button type="button" onClick={() => setPausado((valor) => !valor)} disabled={movimientoReducido || total < 2} className="grid size-11 place-items-center rounded-full border border-brand-on-gradient/25 hover:bg-brand-on-gradient/15 disabled:cursor-not-allowed disabled:opacity-50" aria-label={movimientoReducido ? "La reproducción automática está desactivada por la preferencia de movimiento reducido" : pausado ? "Reanudar reproducción automática" : "Pausar reproducción automática"}>{pausado ? <Play className="size-4" aria-hidden="true" /> : <Pause className="size-4" aria-hidden="true" />}</button>
                </div>
              </div>
              <p className="sr-only" aria-live="polite">Mostrando patrocinador {indice + 1} de {total}: {actual.nombre}</p>
            </div>
          </article>
        </div>
      ) : null}

      <div className="mt-12 flex flex-col gap-6 rounded-3xl border border-primary/12 bg-gradient-to-br from-primary/8 via-surface-raised to-brand-cyan/8 p-6 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-5">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-accent text-accent-foreground shadow-glow-brand">
            <Sparkles className="size-6" aria-hidden="true" />
          </span>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-info">
              {COPY.auspiciadores.invitacion.miniLabel}
            </p>
            <h3 className="mt-2 text-2xl font-black uppercase leading-[1.08] tracking-tight text-foreground sm:text-3xl">
              {COPY.auspiciadores.invitacion.titulo.map((linea, index) => (
                <span key={linea}>
                  {index > 0 && <br />}
                  {linea}
                </span>
              ))}
            </h3>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
              {COPY.auspiciadores.invitacion.descripcion}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setAbierto(true)}
          className="btn-shine inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full bg-accent px-6 text-xs font-black uppercase tracking-wider text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
        >
          {COPY.auspiciadores.invitacion.cta}
          <ArrowUpRight className="size-4" aria-hidden="true" />
        </button>
      </div>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent className="max-w-md">
          <DialogTitle className="text-xl font-black uppercase leading-tight tracking-tight text-foreground">
            TU MARCA.
            <br />
            <span className="text-info">NUESTRA HISTORIA.</span>
          </DialogTitle>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            Conversemos sobre cómo tu marca puede acompañar el reencuentro de
            Salesianos y María Auxiliadora.
          </p>
          <ul className="mt-5 space-y-3">
            {BENEFICIOS.map((beneficio) => (
              <li
                key={beneficio}
                className="flex items-start gap-3 text-sm text-foreground"
              >
                <span
                  aria-hidden="true"
                  className="mt-2 size-1.5 shrink-0 rounded-full bg-primary"
                />
                {beneficio}
              </li>
            ))}
          </ul>
          <p className="mt-5 text-xs leading-relaxed text-muted-foreground">
            Los formatos, beneficios y condiciones se coordinan con la
            organización. Escríbenos por el canal oficial con el nombre de tu
            empresa y la propuesta de participación.
          </p>
          <a
            href={ENLACES.contacto}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-shine mt-6 inline-flex h-12 w-full items-center justify-center gap-2 rounded-full bg-accent px-6 text-xs font-black uppercase tracking-wider text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
          >
            CONTACTAR A LA ORGANIZACIÓN
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </DialogContent>
      </Dialog>
    </PortadaSection>
  );
}
