"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { BadgeCheck, ClipboardCheck, FileCheck, Wallet } from "lucide-react";
import { useEffect, useRef } from "react";

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  {
    num: "01",
    title: "Registra",
    desc: "Completa los datos del responsable, promoción, disciplinas y nómina.",
    icon: ClipboardCheck,
  },
  {
    num: "02",
    title: "Validamos",
    desc: "El Comité revisa elegibilidad, cupo, duplicidades y aceptación de las condiciones vigentes.",
    icon: FileCheck,
  },
  {
    num: "03",
    title: "Paga",
    desc: "Al habilitar izipay recibirás una orden segura por el monto confirmado.",
    icon: Wallet,
  },
  {
    num: "04",
    title: "Compite",
    desc: "Pago conciliado y registro conforme: la inscripción queda confirmada.",
    icon: BadgeCheck,
  },
];

export function Process() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".process-card",
        { y: 50, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.1,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
            once: true,
          },
        },
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section
      id="proceso"
      ref={sectionRef}
      className="flex min-h-screen w-full items-center bg-gradient-to-br from-[#312e8e] to-[#1557b8] py-16 text-white scroll-mt-20 sm:py-24"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <p className="text-center text-sm font-black uppercase tracking-[0.2em] text-white/70">
            Trazabilidad de la preinscripción
          </p>
          <h2 className="mt-4 text-center text-4xl font-black tracking-tight sm:text-5xl">
            De solicitud recibida a equipo confirmado
          </h2>
        </div>

        <div className="process-card mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {STEPS.map((step) => (
            <article
              key={step.num}
              className="card-elevated bg-white p-6 text-[#17214b]"
            >
              <span
                aria-hidden
                className="absolute right-4 top-2 text-6xl font-black text-[#312e8e]/5"
              >
                {step.num}
              </span>
              <div className="flex size-12 items-center justify-center rounded-2xl bg-[#312e8e] text-white shadow-lg shadow-[#312e8e]/20">
                <step.icon className="size-6" />
              </div>
              <h3 className="mt-6 text-xl font-black">{step.title}</h3>
              <p className="mt-3 text-sm leading-7 text-[#626195]">
                {step.desc}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
