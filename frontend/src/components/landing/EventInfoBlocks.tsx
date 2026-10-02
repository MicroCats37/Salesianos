"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  Baby,
  Car,
  Dumbbell,
  Music,
  Moon,
  ShieldCheck,
  Smile,
  Users,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useRef } from "react";

gsap.registerPlugin(ScrollTrigger);

// =============================================================================
// FESTIVAL PARTICLES — smoke clouds + rising sparks (pink/blue/purple/cyan)
// =============================================================================

function FestivalParticles() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sparkRefs = useRef<HTMLSpanElement[]>([]);
  const smokeRefs = useRef<HTMLDivElement[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Rising festival sparks
      sparkRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
          {
            x: gsap.utils.random(-60, 60),
            y: 40,
            opacity: 0,
            scale: gsap.utils.random(0.3, 1),
          },
          {
            x: `+=${gsap.utils.random(-200, 200)}`,
            y: `-=${gsap.utils.random(200, 420)}`,
            opacity: gsap.utils.random(0.4, 0.95),
            scale: gsap.utils.random(0.5, 1.5),
            duration: gsap.utils.random(3.5, 7),
            ease: "sine.out",
            repeat: -1,
            yoyo: false,
            delay: gsap.utils.random(0, 5),
          },
        );
      });

      // Smoke clouds (pink, blue, purple) drifting
      smokeRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
          { opacity: 0, scale: 0.8, filter: "blur(40px)" },
          {
            opacity: gsap.utils.random(0.12, 0.28),
            scale: gsap.utils.random(1.05, 1.35),
            filter: "blur(70px)",
            duration: gsap.utils.random(7, 12),
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true,
            delay: gsap.utils.random(0, 5),
          },
        );
      });
    }, container);

    return () => ctx.revert();
  }, []);

  const sparks = Array.from({ length: 28 });

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-10 overflow-hidden"
    >
      {/* Smoke clouds — festival colors */}
      <div
        ref={(el) => {
          if (el) smokeRefs.current[0] = el;
        }}
        className="absolute -left-32 top-10 h-[50vh] w-[50vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(236,72,153,0.55), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[1] = el;
        }}
        className="absolute -right-32 top-1/3 h-[45vh] w-[45vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(99,102,241,0.5), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[2] = el;
        }}
        className="absolute left-1/4 bottom-0 h-[40vh] w-[40vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(34,211,238,0.45), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[3] = el;
        }}
        className="absolute right-1/4 top-1/2 h-[35vh] w-[35vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(192,132,252,0.35), transparent 70%)",
        }}
      />

      {/* Sparks */}
      {sparks.map((_, i) => {
        const colors = [
          "rgba(236,72,153,0.9)",  // pink
          "rgba(99,102,241,0.9)",  // purple
          "rgba(34,211,238,0.9)",   // cyan
          "rgba(192,132,252,0.85)", // violet
        ];
        const color = colors[i % colors.length];
        const size = (i % 3 === 0) ? 5 : (i % 3 === 1) ? 4 : 3;
        return (
          <span
            key={i}
            ref={(el) => {
              if (el) sparkRefs.current[i] = el;
            }}
            className="absolute rounded-full"
            style={{
              left: `${(i * 47) % 100}%`,
              bottom: `${(i * 19) % 35}%`,
              width: size,
              height: size,
              background: color,
              boxShadow: `0 0 ${size * 2}px ${color}`,
            }}
          />
        );
      })}
    </div>
  );
}

// =============================================================================
// BLOCK DATA
// =============================================================================

const BLOCKS = [
  {
    id: "por-que-festival",
    eyebrow: "Festival Deportivo",
    title: "¿Por qué un Festival?",
    pill: "El reencuentro que tu promoción merece",
    body: "Frente al formato tradicional de campeonato, el Festival Deportivo Salesianos transforma la competencia en una experiencia de hermandad. No es solo jugar — es volver a encontrarnos, compartir con nuestras familias y celebrar juntos lo que significa ser parte de esta comunidad.",
    ribbon: "Del torneo a la fiesta: así se vive el reencuentro en Salesianos.",
    bullets: [
      { icon: Users, color: "#ec4899", text: "Reencuentro con compañeros de promoción" },
      { icon: Smile, color: "#22d3ee", text: "Ambiente festivo, no competitivo excluyente" },
      { icon: Music, color: "#6366f1", text: "Música, comida y espacio para todos" },
      { icon: Baby, color: "#ec4899", text: "Actividades para niños y familiares" },
    ],
    images: [
      "/images/fulbito-varones.webp",
      "/images/voley-mixto.webp",
    ],
  },
  {
    id: "familia-convivencia",
    eyebrow: "Familia y Convivencia",
    title: "Un festival para toda la familia",
    pill: "Donde los menores también son protagonistas",
    body: "A diferencia de los torneos convencionales, el Festival Salesianos abre sus puertas a toda la familia. Habrá ambientes seguros para niños, actividades recreativas y un espacio diseñado para que nadie quede fuera de la celebración.",
    ribbon: "Porque el deporte que nos une, nos incluye a todos.",
    bullets: [
      { icon: Baby, color: "#22d3ee", text: "Área de juegos infantiles vigilada" },
      { icon: Users, color: "#ec4899", text: "Espacios seguros para toda la familia" },
      { icon: Smile, color: "#6366f1", text: "Actividades recreativas intergeneracionales" },
      { icon: ShieldCheck, color: "#22d3ee", text: "Protocolos de seguridad y bienestar" },
    ],
    images: [
      "/images/basket-varones.webp",
      "/images/fulbito-varones.webp",
    ],
  },
  {
    id: "infraestructura",
    eyebrow: "Infraestructura",
    title: "Instalaciones deportivas de primera",
    pill: "Canchas, iluminación y servicios certificados",
    body: "Contamos con infraestructura deportiva adecuada para cada disciplina: campos de grass sintético,los mejoresstandares en iluminacion, camerinos limpios y un salón techado para actividades nocturnas y ceremonias. Todo pensado para la comodidad de los participantes.",
    ribbon: "Canchas en optimas condiciones: así se compite en Salesianos.",
    bullets: [
      { icon: Dumbbell, color: "#6366f1", text: "Canchas de grass sintético de alta calidad" },
      { icon: Moon, color: "#ec4899", text: "Iluminación LED para partidos nocturnos" },
      { icon: ShieldCheck, color: "#22d3ee", text: "Camerinos y servicios higiene impecable" },
      { icon: Music, color: "#6366f1", text: "Salón techado para ceremonias y eventos" },
    ],
    images: [
      "/images/voley-mixto.webp",
      "/images/basket-varones.webp",
    ],
  },
  {
    id: "noche",
    eyebrow: "Y cuando caiga la noche",
    title: "La fiesta continúa bajo las estrellas",
    pill: "Del campo al salón de eventos",
    body: "Una vez que el sol se esconde, el Festival Salesianos se transforma. BBQ, música en vivo, open bar para adultos y un ambiente de fraternidad que solo se vive en las grandes reuniones de exalumnos. No es torneo — es celebración.",
    ribbon: "Del campeonato a la fiesta: la noche es nuestra.",
    bullets: [
      { icon: Music, color: "#ec4899", text: "Música en vivo y DJ toda la noche" },
      { icon: Smile, color: "#22d3ee", text: "BBQ y comida tradicional peruana" },
      { icon: Moon, color: "#6366f1", text: "Ambiente iluminado y seguro" },
      { icon: Users, color: "#ec4899", text: "Networking entre promociones" },
    ],
    images: [
      "/images/fulbito-varones.webp",
      "/images/voley-mixto.webp",
    ],
  },
  {
    id: "comodidad",
    eyebrow: "Comodidad para Todos",
    title: "Estacionamiento, higiene y seguridad",
    pill: "Sin preocupaciones, solo diversión",
    body: "Sabemos que la experiencia completa empieza desde el arrival. Por eso gestionamos estacionamiento vigilado, servicios hygiene de primer nivel, atención médica de emergencia y un equipo de apoyo dedicado a que cada familia pueda disfrutar sin pensar en logística.",
    ribbon: "Llega, estaciona y disfruta: aquí pensamos en todo.",
    bullets: [
      { icon: Car, color: "#22d3ee", text: "Estacionamiento vigilado gratuito" },
      { icon: ShieldCheck, color: "#6366f1", text: "Primeros auxilios y ambulancia en sitio" },
      { icon: Dumbbell, color: "#ec4899", text: "Baños limpios y suficientes para todos" },
      { icon: Users, color: "#22d3ee", text: "Equipo de apoyo y coordinación en sitio" },
    ],
    images: [
      "/images/basket-varones.webp",
      "/images/voley-mixto.webp",
    ],
  },
];

// =============================================================================
// INFO BLOCK — individual section block with collage + ribbon
// =============================================================================

function InfoBlock({
  block,
  index,
}: {
  block: (typeof BLOCKS)[number];
  index: number;
}) {
  const blockRef = useRef<HTMLDivElement>(null);
  const isReversed = index % 2 === 1;

  useEffect(() => {
    if (!blockRef.current) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Main content slide in from side
      gsap.fromTo(
        ".block-content",
        { x: isReversed ? 60 : -60, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.9,
          ease: "power3.out",
          scrollTrigger: {
            trigger: blockRef.current,
            start: "top 80%",
            once: true,
          },
        },
      );

      // Collage slide from opposite side
      gsap.fromTo(
        ".block-collage",
        { x: isReversed ? -60 : 60, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.9,
          ease: "power3.out",
          delay: 0.15,
          scrollTrigger: {
            trigger: blockRef.current,
            start: "top 80%",
            once: true,
          },
        },
      );

      // Ribbon line reveal
      gsap.fromTo(
        ".block-ribbon",
        { y: 20, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.6,
          ease: "power2.out",
          delay: 0.3,
          scrollTrigger: {
            trigger: blockRef.current,
            start: "top 75%",
            once: true,
          },
        },
      );

      // Bullets stagger
      gsap.fromTo(
        ".block-bullet",
        { x: isReversed ? 30 : -30, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.08,
          ease: "power2.out",
          delay: 0.2,
          scrollTrigger: {
            trigger: blockRef.current,
            start: "top 78%",
            once: true,
          },
        },
      );
    }, blockRef);

    return () => ctx.revert();
  }, [isReversed]);

  return (
    <div
      id={block.id}
      ref={blockRef}
      className="relative overflow-hidden py-20 scroll-mt-24 sm:py-28"
    >
      {/* Alternating background */}
      <div
        className={`absolute inset-0 -z-10 ${
          index % 2 === 0
            ? "bg-gradient-to-br from-[#0c0c1f] via-[#1a1857] to-[#0c0c1f]"
            : "bg-gradient-to-br from-[#17214b] via-[#0c0c1f] to-[#17214b]"
        }`}
      />

      <div className="relative z-20 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div
          className={`grid gap-12 lg:grid-cols-2 lg:gap-16 items-center ${
            isReversed ? "lg:flex-row-reverse" : ""
          }`}
        >
          {/* LEFT — Content */}
          <div className="block-content">
            {/* Eyebrow */}
            <span className="inline-block rounded-full border border-white/20 bg-white/5 px-4 py-1.5 text-xs font-black uppercase tracking-[0.2em] text-white/70 backdrop-blur">
              {block.eyebrow}
            </span>

            {/* Headline */}
            <h2 className="mt-5 text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-4xl xl:text-5xl">
              {block.title}
            </h2>

            {/* Pill subheading */}
            <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#22d3ee]/40 bg-[#22d3ee]/10 px-5 py-2 text-sm font-bold text-[#22d3ee]">
              <span className="size-2 rounded-full bg-[#22d3ee] animate-pulse" />
              {block.pill}
            </div>

            {/* Body */}
            <p className="mt-6 max-w-xl text-base leading-8 text-white/75 lg:text-lg">
              {block.body}
            </p>

            {/* Bullet list */}
            <ul className="mt-8 space-y-4">
              {block.bullets.map((bullet, i) => (
                <li key={i} className="block-bullet flex items-start gap-3">
                  <span
                    className="mt-1 grid size-7 shrink-0 place-items-center rounded-full"
                    style={{ backgroundColor: `${bullet.color}22`, border: `1px solid ${bullet.color}55` }}
                  >
                    <bullet.icon className="size-4" style={{ color: bullet.color }} />
                  </span>
                  <span className="text-sm leading-6 text-white/80">{bullet.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* RIGHT — Image Collage */}
          <div className="block-collage">
            <div className="relative">
              {/* Main image */}
              <div className="overflow-hidden rounded-3xl border border-white/10 shadow-2xl shadow-black/40">
                <Image
                  src={block.images[0]}
                  alt={block.title}
                  width={640}
                  height={400}
                  className="w-full object-cover"
                  style={{ height: "320px" }}
                />
              </div>
              {/* Secondary image — stacked offset */}
              <div className="absolute -bottom-8 -right-6 w-48 overflow-hidden rounded-2xl border border-white/10 shadow-xl shadow-black/30 sm:w-56">
                <Image
                  src={block.images[1] ?? block.images[0]}
                  alt=""
                  width={280}
                  height={180}
                  className="w-full object-cover"
                  style={{ height: "160px" }}
                />
              </div>
              {/* Decorative accent */}
              <div
                className="absolute -top-4 -left-4 size-24 rounded-2xl border border-white/10 bg-white/5 backdrop-blur"
                aria-hidden
              />
            </div>
          </div>
        </div>

        {/* Ribbon closing line */}
        <div className="block-ribbon mt-16 rounded-2xl border border-[#22d3ee]/30 bg-gradient-to-r from-[#22d3ee]/10 via-[#312e8e]/20 to-[#22d3ee]/10 p-5 text-center backdrop-blur">
          <p className="text-base font-bold text-[#22d3ee] sm:text-lg">
            {block.ribbon}
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SECTION — EventInfoBlocks with particles + rotating title
// =============================================================================

export function EventInfoBlocks() {
  const sectionRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Section header entrance
      gsap.fromTo(
        ".section-header",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".section-header",
            start: "top 85%",
            once: true,
          },
        },
      );

      // Rotating word animation in title
      if (titleRef.current) {
        const words = titleRef.current.querySelectorAll(".rotate-word");
        let idx = 0;
        gsap.fromTo(
          titleRef.current,
          { opacity: 0 },
          { opacity: 1, duration: 0.5, ease: "power2.out" },
        );

        function cycleWords() {
          gsap.to(words, {
            opacity: 0,
            y: -15,
            duration: 0.25,
            ease: "power2.in",
            onComplete: () => {
              idx = (idx + 1) % words.length;
              words.forEach((w, i) => {
                gsap.set(w, { y: i === idx ? 15 : 0 });
              });
              gsap.to(words[idx], {
                opacity: 1,
                y: 0,
                duration: 0.35,
                ease: "power2.out",
                onComplete: () => {
                  gsap.delayedCall(2.5, cycleWords);
                },
              });
            },
          });
        }

        gsap.delayedCall(3, cycleWords);
      }
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      id="festival"
      ref={sectionRef}
      className="relative overflow-hidden"
    >
      {/* Festival particles background */}
      <FestivalParticles />

      {/* Header */}
      <div className="section-header relative z-20 mx-auto max-w-4xl px-4 pt-20 text-center sm:px-6 lg:px-8">
        <p className="text-sm font-black uppercase tracking-[0.25em] text-[#ec4899]">
          La experiencia Salesianos
        </p>
        <h2 className="mt-4 text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl">
          Más que un torneo,{" "}
          <span ref={titleRef} className="inline-block">
            <span className="rotate-word absolute text-gradient-festival">
              una fiesta
            </span>
            <span className="rotate-word absolute text-gradient-festival">
              un reencuentro
            </span>
            <span className="rotate-word absolute text-gradient-festival">
              una comunidad
            </span>
            <span className="rotate-word text-gradient-festival">un festival</span>
          </span>
        </h2>
        <p className="mt-6 text-lg leading-8 text-white/70">
          El Festival Deportivo Salesianos 2026 combina competencia, familia y
          celebración en un solo evento diseñado para toda la promoción.
        </p>
      </div>

      {/* Block sections */}
      <div className="mt-16">
        {BLOCKS.map((block, index) => (
          <InfoBlock key={block.id} block={block} index={index} />
        ))}
      </div>
    </section>
  );
}
