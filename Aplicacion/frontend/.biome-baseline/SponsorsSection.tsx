"use client";

import { ArrowUpRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { AUSPICIADORES, ENLACES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";

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

  return (
    <PortadaSection
      id="auspiciadores"
      eyebrow={COPY.auspiciadores.eyebrow}
      titulo={[...COPY.auspiciadores.titulo]}
      destacado={COPY.auspiciadores.destacado}
      copy={COPY.auspiciadores.copy}
    >
      {AUSPICIADORES.length > 0 && (
        <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {AUSPICIADORES.map((auspiciador) => (
            <li
              key={auspiciador.nombre}
              className="card-elevated rounded-2xl p-5"
            >
              <a
                href={auspiciador.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-3 text-sm font-black uppercase tracking-tight text-[#17214b]"
              >
                {auspiciador.nombre}
                <ArrowUpRight className="size-4" aria-hidden="true" />
              </a>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-12 flex flex-col gap-6 rounded-3xl border border-[#312e8e]/12 bg-gradient-to-br from-[#312e8e]/8 via-white to-[#22d3ee]/8 p-6 sm:p-10 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-5">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[#312e8e] text-[#f4c64e] shadow-lg">
            <Sparkles className="size-6" aria-hidden="true" />
          </span>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-[#1557b8]">
              {COPY.auspiciadores.invitacion.miniLabel}
            </p>
            <h3 className="mt-2 text-2xl font-black uppercase leading-[1.08] tracking-tight text-[#17214b] sm:text-3xl">
              {COPY.auspiciadores.invitacion.titulo.map((linea, index) => (
                <span key={linea}>
                  {index > 0 && <br />}
                  {linea}
                </span>
              ))}
            </h3>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-[#626195]">
              {COPY.auspiciadores.invitacion.descripcion}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setAbierto(true)}
          className="btn-brand-gradient btn-shine inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
        >
          {COPY.auspiciadores.invitacion.cta}
          <ArrowUpRight className="size-4" aria-hidden="true" />
        </button>
      </div>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent className="max-w-md">
          <DialogTitle className="text-xl font-black uppercase leading-tight tracking-tight text-[#17214b]">
            TU MARCA.
            <br />
            <span className="text-[#1557b8]">NUESTRA HISTORIA.</span>
          </DialogTitle>
          <p className="mt-4 text-sm leading-relaxed text-[#626195]">
            Conversemos sobre cómo tu marca puede acompañar el reencuentro de
            Salesianos y María Auxiliadora.
          </p>
          <ul className="mt-5 space-y-3">
            {BENEFICIOS.map((beneficio) => (
              <li
                key={beneficio}
                className="flex items-start gap-3 text-sm text-[#17214b]"
              >
                <span
                  aria-hidden="true"
                  className="mt-2 size-1.5 shrink-0 rounded-full bg-[#312e8e]"
                />
                {beneficio}
              </li>
            ))}
          </ul>
          <p className="mt-5 text-xs leading-relaxed text-[#626195]">
            Los formatos, beneficios y condiciones se coordinan con la
            organización. Escríbenos por el canal oficial con el nombre de tu
            empresa y la propuesta de participación.
          </p>
          <a
            href={ENLACES.contacto}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-brand-gradient btn-shine mt-6 inline-flex h-12 w-full items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
          >
            CONTACTAR A LA ORGANIZACIÓN
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </DialogContent>
      </Dialog>
    </PortadaSection>
  );
}
