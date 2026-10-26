"use client";

import { ArrowUpRight, Ticket } from "lucide-react";
import Image from "next/image";
import { useEffect, useState } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ENLACES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";
import { estado } from "@/features/portada/pricing-stage";

/**
 * Pase individual para asistir solo a la fiesta.
 *
 * El precio depende de la etapa de venta: S/ 25 en preventa y S/ 35 en
 * puerta una vez cerrada.
 */
export function PartyPassSection() {
  const [enPreventa, setEnPreventa] = useState(
    () => estado().key === "preventa",
  );
  const [abierto, setAbierto] = useState(false);

  useEffect(() => {
    const intervalo = setInterval(() => {
      setEnPreventa(estado().key === "preventa");
    }, 60_000);
    return () => clearInterval(intervalo);
  }, []);

  const precio = enPreventa
    ? COPY.paseFiesta.precioPreventa
    : COPY.paseFiesta.precioPuerta;

  return (
    <PortadaSection id={COPY.paseFiesta.id} fondo="marca">
      <div className="mt-12 grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-12">
        <div className="relative overflow-hidden rounded-2xl border border-white/15">
          <div className="relative aspect-[4/5] w-full sm:aspect-[16/10] lg:aspect-[4/5]">
            <Image
              src="/images/portada/pase-fiesta.webp"
              alt="Afiche oficial del pase individual para la fiesta de Salesianos FEST"
              fill
              loading="lazy"
              sizes="(max-width: 1024px) 100vw, 50vw"
              className="object-cover"
            />
          </div>
        </div>

        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-sky-300">
            {COPY.paseFiesta.miniLabel}
          </p>
          <h2 className="mt-3 text-3xl font-black uppercase leading-[1.05] tracking-tight text-white sm:text-4xl">
            {COPY.paseFiesta.titulo.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {linea}
              </span>
            ))}
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-white/75 sm:text-base">
            {COPY.paseFiesta.copy}
          </p>

          <div className="mt-8 flex flex-wrap items-end gap-x-4 gap-y-2">
            <span className="text-4xl font-black leading-none text-white sm:text-5xl">
              S/ {precio}
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-sky-300">
              {enPreventa
                ? "Preventa por persona · Hasta el 25 de octubre"
                : "Por persona · Precio en puerta"}
            </span>
          </div>
          {enPreventa && (
            <p className="mt-2 text-xs text-white/60">
              Precio anunciado en puerta: S/ {COPY.paseFiesta.precioPuerta} por
              persona.
            </p>
          )}

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => setAbierto(true)}
              className="btn-brand-gradient btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
            >
              <Ticket className="size-4" aria-hidden="true" />
              {COPY.paseFiesta.cta}
            </button>
            <a
              href={ENLACES.facebook}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-white/30 px-5 text-xs font-black uppercase tracking-wider text-white transition-colors hover:bg-white/10"
            >
              {COPY.paseFiesta.enlaceAnuncio}
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent className="max-w-lg">
          <DialogTitle className="text-lg font-black uppercase tracking-tight">
            {COPY.paseFiesta.titulo.join(" ")}
          </DialogTitle>
          <div className="relative mt-4 overflow-hidden rounded-xl">
            <Image
              src="/images/portada/pase-fiesta.webp"
              alt="Afiche oficial del pase individual para la fiesta"
              width={900}
              height={1200}
              className="h-auto w-full object-cover"
            />
          </div>
          <p className="mt-4 text-sm leading-relaxed text-[#626195]">
            S/ {precio} por persona.{" "}
            {enPreventa
              ? "Preventa hasta el 25 de octubre a las 8:00 p. m."
              : "La preventa de S/ 25 finalizó; el precio anunciado en puerta es S/ 35."}
          </p>
          <a
            href={ENLACES.contacto}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-brand-gradient btn-shine mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
          >
            CONSULTAR POR WHATSAPP
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </DialogContent>
      </Dialog>
    </PortadaSection>
  );
}
