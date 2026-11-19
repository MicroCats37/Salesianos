"use client";

import { ArrowRight, Info } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PaqueteComercialCard } from "@/components/paquetes/PaqueteComercialCard";
import { PreventaBanner } from "@/components/paquetes/PreventaBanner";
import type { EtapaPrecio } from "@/components/paquetes/paquete-copy";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { useLandingPaquetes } from "@/features/landing/hooks/useLandingPaquetes";
import { ENLACES, SECCIONES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";
import { estado } from "@/features/portada/pricing-stage";
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
      <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div
          role="tablist"
          aria-label="Tipo de inscripción"
          className="flex w-full gap-2 rounded-full bg-white/70 p-1 sm:w-auto"
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
                    ? "bg-[#312e8e] text-white shadow-lg shadow-[#312e8e]/20"
                    : "text-[#312e8e] hover:bg-[#312e8e]/5",
                )}
              >
                {opcion.label}
              </button>
            );
          })}
        </div>

        <p className="inline-flex items-center gap-2 rounded-full border border-[#312e8e]/15 bg-white/70 px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#312e8e]">
          <span
            className={cn(
              "size-2 rounded-full",
              etapa === "consultar" ? "bg-slate-400" : "bg-emerald-500",
            )}
            aria-hidden="true"
          />
          {estadoVenta.etiqueta}
        </p>
      </div>

      <div className="relative mt-8">
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
              className="h-[30rem] animate-pulse rounded-2xl bg-white/60"
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
                  className="btn-brand-gradient btn-shine flex h-12 w-full items-center justify-center gap-2 rounded-full px-5 text-xs font-black uppercase tracking-wider"
                >
                  {ctaPrimario.label}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </a>
              }
            />
          ))}
        </div>
      )}

      <div className="mt-8 flex flex-col gap-3 border-t border-[#312e8e]/15 pt-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex max-w-2xl items-start gap-2 text-xs leading-relaxed text-[#626195]">
          <Info
            className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
            aria-hidden="true"
          />
          {COPY.paquetes.disclaimer}
        </p>
        <a
          href="/login"
          className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
        >
          {COPY.paquetes.enlaceCuenta}
          <ArrowRight className="size-4" aria-hidden="true" />
        </a>
      </div>

      <ol className="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {COPY.paquetes.calendario.map((paso) => (
          <li
            key={paso.numero}
            className="card-elevated rounded-2xl p-5 sm:p-6"
          >
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1557b8]">
              {paso.numero}
            </span>
            <h3 className="mt-2 text-lg font-black uppercase tracking-tight text-[#17214b]">
              {paso.titulo}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-[#626195]">
              {paso.descripcion}
            </p>
            <p className="mt-3 text-xs font-bold text-[#17214b]">
              {paso.cierre}
            </p>
          </li>
        ))}
      </ol>
    </PortadaSection>
  );
}
