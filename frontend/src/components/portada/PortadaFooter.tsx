"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowUpRight, Camera, Music2, Share2 } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { ENLACES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";

gsap.registerPlugin(ScrollTrigger);

const REDES = [
  { label: "Facebook", href: ENLACES.facebook, Icon: Share2 },
  { label: "Instagram", href: ENLACES.instagram, Icon: Camera },
  { label: "TikTok", href: ENLACES.tiktok, Icon: Music2 },
];

/**
 * Pie de la portada.
 *
 * Reúne la marca, la promesa, las redes y los datos de la organización.
 */
export function PortadaFooter() {
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.from("[data-footer-stagger]", {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: "power3.out",
        immediateRender: false,
        scrollTrigger: { trigger: root, start: "top 80%", once: true },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <footer
      ref={rootRef}
      className="border-t border-white/10 bg-[#0c0c1f] py-14 text-white"
    >
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-3">
          <div data-footer-stagger>
            <Image
              src="/images/portada/wordmark.png"
              alt="Salesianos FEST"
              width={640}
              height={196}
              className="h-10 w-auto brightness-0 invert"
            />
            <p className="mt-5 text-sm leading-relaxed text-white/65">
              {COPY.footer.frase.map((linea) => (
                <span key={linea} className="block">
                  {linea}
                </span>
              ))}
            </p>
          </div>

          <div data-footer-stagger>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-[#f4c64e]">
              Síguenos
            </p>
            <ul className="mt-5 space-y-3">
              {REDES.map(({ label, href, Icon }) => (
                <li key={label}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-white/75 transition-colors hover:text-white"
                  >
                    <Icon className="size-4" aria-hidden="true" />
                    {label}
                    <ArrowUpRight className="size-3.5" aria-hidden="true" />
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div data-footer-stagger>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-[#22d3ee]">
              Inscripciones
            </p>
            <a
              href={ENLACES.contacto}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-5 inline-flex items-center gap-2 text-sm font-black uppercase tracking-wider text-white transition-colors hover:text-[#f4c64e]"
            >
              {COPY.footer.inscripciones}
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
            <p className="mt-5 text-xs leading-relaxed text-white/50">
              {COPY.footer.copyright}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-white/50">
              {COPY.footer.organiza}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
