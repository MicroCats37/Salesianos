"use client";

import { ArrowRight, Info } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PaqueteComercialCard } from "@/features/portada/components/PaqueteComercialCard";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { PreventaBanner } from "@/features/portada/components/PreventaBanner";
import type { EtapaPrecio } from "@/features/portada/components/paquete-copy";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES, SECCIONES } from "@/features/portada/fixtures/festival";
import { estado } from "@/features/portada/fixtures/pricing-stage";
import { useLandingPaquetes } from "@/features/portada/fixtures/useLandingPaquetes";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";

type TabPaquetes = "packs" | "sports";

/**
 * Etapa de venta vigente, refrescada cada minuto.
 *
 * Solo cambia el re-render cuando cambia la etapa: mientras la ventana no
 * se mueva, las tarjetas no se vuelven a pintar.
 */
function useEtapaPrecio(): EtapaPrecio {
  const [etapa, setEtapa] = useState<EtapaPrecio>(() => {
    const actual = estado().key;
    if (actual === "preventa") return "preventa";
    if (actual === "regular") return "regular";
    return "consultar";
  });

  useEffect(() => {
    const intervalo = setInterval(() => {
      const actual = estado().key;
      const siguiente: EtapaPrecio =
        actual === "preventa"
          ? "preventa"
          : actual === "regular"
            ? "regular"
            : "consultar";
      setEtapa((previa) => (previa === siguiente ? previa : siguiente));
    }, 60_000);
    return () => clearInterval(intervalo);
  }, []);

  return etapa;
}

/**
 * Sección "05 / ELIGE CÓMO VIVIRLO".
 *
 * Las tarjetas son las mismas que usa `/informacion` (`PaqueteComercialCard`),
 * pero aquí el importe depende de la etapa de venta vigente.
 */
export function TicketsSection() {
  const [tab, setTab] = useState<TabPaquetes>("packs");
  const { data: paquetes, isLoading } = useLandingPaquetes();
  const etapa = useEtapaPrecio();
  const estadoVenta = estado();

  const visibles = useMemo(() => {
    const lista = paquetes ?? [];
    return lista.filter((paquete) =>
      tab === "packs" ? paquete.tipo === "PACK" : paquete.tipo === "DISCIPLINA",
    );
  }, [paquetes, tab]);

  const ctaPrimario =
    etapa === "consultar"
      ? {
          label: "CONSULTAR A LA ORGANIZACIÓN",
          href: ENLACES.contacto,
          externo: true,
        }
      : {
          label: "INSCRIBIR EQUIPO",
          href: ENLACES.registro,
          externo: false,
        };

  return (
    <PortadaSection
      id={SECCIONES.paquetes}
      eyebrow={COPY.paquetes.eyebrow}
      titulo={[...COPY.paquetes.titulo]}
      destacado={COPY.paquetes.destacado}
      copy={[...COPY.paquetes.copy]}
    >
      {/*
        Las pestañas y el estado de venta van JUNTOS: separados por todo el
        ancho, el distintivo de "inscripciones finalizadas" quedaba solo en
        la esquina derecha y la fila se leía como medio vacía.
      */}
      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-5 [@media(max-height:900px)]:mt-5">
        <div
          role="tablist"
          aria-label="Tipo de inscripción"
          className="flex w-full gap-2 rounded-full bg-surface-raised/70 p-1 sm:w-auto"
        >
          {COPY.paquetes.tabs.map((opcion) => {
            const activa = opcion.id === tab;
            return (
              <button
                key={opcion.id}
                type="button"
                role="tab"
                aria-selected={activa}
                onClick={() => setTab(opcion.id)}
                className={cn(
                  "h-12 flex-1 whitespace-nowrap rounded-full px-5 text-xs font-black uppercase tracking-wider transition-colors sm:flex-none",
                  activa
                    ? "bg-brand-gradient-deep text-brand-on-gradient"
                    : "text-primary hover:bg-primary/5",
                )}
              >
                {opcion.label}
              </button>
            );
          })}
        </div>

        <p className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/15 bg-surface-raised/70 px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary">
          <span
            className={cn(
              "size-2 rounded-full",
              etapa === "consultar" ? "bg-muted-foreground" : "bg-success",
            )}
            aria-hidden="true"
          />
          {estadoVenta.etiqueta}
        </p>
      </div>

      <div className="relative mt-6 [@media(max-height:900px)]:mt-4">
        <PreventaBanner
          titulo="PREVENTA POR"
          palabraDestacada={tab === "packs" ? "PACKS" : "DISCIPLINA"}
          variant={tab === "packs" ? "PACKS" : "DISCIPLINA"}
          className="-mx-4 sm:-mx-6 lg:-mx-8"
        />
      </div>

      {isLoading ? (
        <div className="relative z-30 -mt-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((item) => (
            <div
              key={item}
              className="h-[30rem] animate-pulse rounded-2xl bg-surface-raised/60"
            />
          ))}
        </div>
      ) : (
        <div className="relative z-30 -mt-10 grid grid-cols-1 items-stretch gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {visibles.map((paquete) => (
            <PaqueteComercialCard
              key={paquete.id}
              paquete={paquete}
              variant={paquete.tipo}
              etapa={etapa}
              footer={
                <a
                  href={ctaPrimario.href}
                  {...(ctaPrimario.externo
                    ? { target: "_blank", rel: "noopener noreferrer" }
                    : {})}
                  className="btn-shine flex h-12 w-full items-center justify-center gap-2 rounded-full bg-accent px-5 text-xs font-black uppercase tracking-wider text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
                >
                  {ctaPrimario.label}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </a>
              }
            />
          ))}
        </div>
      )}

      <div className="mt-8 flex flex-col gap-3 border-t border-primary/15 pt-6 sm:flex-row sm:items-center sm:justify-between [@media(max-height:900px)]:mt-5">
        <p className="flex max-w-2xl items-start gap-2 text-xs leading-relaxed text-muted-foreground">
          <Info
            className="mt-0.5 size-4 shrink-0 text-primary"
            aria-hidden="true"
          />
          {COPY.paquetes.disclaimer}
        </p>
        <a
          href={RUTAS.auth.login}
          className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
        >
          {COPY.paquetes.enlaceCuenta}
          <ArrowRight className="size-4" aria-hidden="true" />
        </a>
      </div>

      <ol className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4 [@media(max-height:900px)]:mt-6">
        {COPY.paquetes.calendario.map((paso) => (
          <li
            key={paso.numero}
            className="card-elevated rounded-2xl p-5 sm:p-6"
          >
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-info">
              {paso.numero}
            </span>
            <h3 className="mt-2 text-lg font-black uppercase tracking-tight text-foreground">
              {paso.titulo}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {paso.descripcion}
            </p>
            <p className="mt-3 text-xs font-bold text-foreground">
              {paso.cierre}
            </p>
          </li>
        ))}
      </ol>
    </PortadaSection>
  );
}
