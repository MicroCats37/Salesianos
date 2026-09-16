"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

gsap.registerPlugin(ScrollTrigger);

const FAQ = [
  {
    q: "¿Cuándo una inscripción queda confirmada?",
    a: "Cuando el formulario está completo, la nómina sea validada contra el carné o padrón oficial, las bases hayan sido aceptadas y el pago del paquete figure conciliado.",
  },
  {
    q: "¿Una promoción puede participar en más de una disciplina?",
    a: "Sí. El paquete permite registrar un equipo por promoción en cada disciplina. Cada deportista debe quedar asociado a sus disciplinas y no puede integrar otro equipo de la misma disciplina.",
  },
  {
    q: "¿Cuáles son las categorías y el máximo de jugadores?",
    a: "La plataforma aplica los rangos de promoción indicados en los artículos 14, 20 y 26, además de los máximos de 12 integrantes para fulbito y vóley y 10 para básquet.",
  },
  {
    q: "¿Qué ocurre si un documento aparece dos veces?",
    a: "La plataforma bloquea duplicados dentro de la misma nómina. El Comité también revisará cruces entre equipos antes de aprobar cada inscripción.",
  },
  {
    q: "¿Cómo se atenderán observaciones?",
    a: "El responsable recibirá la observación por el correo o WhatsApp declarado. La solicitud permanecerá en revisión hasta que la nómina o los documentos sean subsanados.",
  },
  {
    q: "¿Ya se puede pagar con izipay?",
    a: "El módulo está preparado para crear la orden después de la validación. Permanece deshabilitado hasta completar credenciales y pruebas. La tarifa regular indicada en las bases es S/ 1,350; anticipada y extemporánea están pendientes de definición.",
  },
];

export function Reglamento() {
  const [open, setOpen] = useState<number | null>(0);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".reglamento-reveal",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.12,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 80%",
            once: true,
          },
        },
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section
      id="reglamento"
      ref={sectionRef}
      className="bg-white py-20 scroll-mt-20 sm:py-24"
    >
      <div className="mx-auto grid max-w-7xl gap-12 px-4 sm:px-6 lg:grid-cols-[0.76fr_1.24fr] lg:px-8">
        <div className="reglamento-reveal">
          <p className="text-sm font-black uppercase tracking-[0.2em] text-[#312e8e]/70">
            Criterios de inscripción
          </p>
          <h2 className="mt-4 text-4xl font-black tracking-tight text-[#17214b] sm:text-5xl">
            Condiciones de preinscripción aplicadas
          </h2>
          <p className="mt-5 text-lg leading-8 text-[#626195]">
            La plataforma registra la versión aceptada de las bases, controla
            topes de nómina y evita confirmar equipos antes de validar la
            acreditación salesiana y conciliar el pago.
          </p>
          <div className="reglamento-reveal mt-7 rounded-2xl border border-[#f4c64e]/45 bg-[#fff9df] p-5 text-sm leading-6 text-[#665010]">
            <strong className="block text-[#3d330f]">
              BASES-SF26-2026-09-06
            </strong>
            Documento aprobado el 5 de septiembre de 2026 por las Juntas
            Directivas de la Promoción 2002 — MA y SJB. Los puntos marcados como
            pendientes en el documento requieren precisión del Comité.
          </div>
        </div>

        <div className="reglamento-reveal rounded-[1.75rem] border border-[#312e8e]/10 bg-white px-6 shadow-xl shadow-[#1f2357]/8">
          {FAQ.map((item, idx) => (
            <div
              key={idx}
              className="border-b border-[#312e8e]/10 last:border-0"
            >
              <button
                type="button"
                className="flex w-full items-center justify-between gap-4 py-5 text-left text-base font-black text-[#17214b] hover:no-underline"
                onClick={() => setOpen(open === idx ? null : idx)}
              >
                {item.q}
                <ChevronDown
                  className={`size-4 shrink-0 transition-transform ${open === idx ? "rotate-180" : ""}`}
                />
              </button>
              {open === idx && (
                <div className="pb-5 text-base leading-7 text-[#626195]">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
