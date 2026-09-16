"use client";

import useEmblaCarousel from "embla-carousel-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

gsap.registerPlugin(ScrollTrigger);

const IMAGES = [
  {
    src: "/images/fulbito-varones.webp",
    label: "Fulbito Varones — Adulto",
    caption: "Súper Máster confraternidad",
  },
  {
    src: "/images/voley-mixto.webp",
    label: "Vóley Mixto — Jóvenes",
    caption: "Promoción 2002 · Sábado 21 Nov",
  },
  {
    src: "/images/basket-varones.webp",
    label: "Básquet Varones — Júnior",
    caption: "Cuadrangular Salesianos FEST 2026",
  },
  {
    src: "/images/fulbito-dam.webp",
    label: "Fulbito Damas — Súper Máster",
    caption: "Confraternidad deportiva",
  },
];

export function Gallery() {
  const sectionRef = useRef<HTMLElement>(null);
  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true, align: "start" });

  // Autoplay with interval
  useEffect(() => {
    if (!emblaApi) return;

    let intervalId: ReturnType<typeof setInterval>;
    let isPaused = false;

    const startAutoplay = () => {
      intervalId = setInterval(() => {
        if (!isPaused && emblaApi) {
          emblaApi.scrollNext();
        }
      }, 4000);
    };

    const stopAutoplay = () => clearInterval(intervalId);

    // Pause on hover
    const onMouseEnter = () => {
      isPaused = true;
    };
    const onMouseLeave = () => {
      isPaused = false;
    };

    const emblaEl = emblaApi.slideNodes()[0]?.parentElement;
    emblaEl?.addEventListener("mouseenter", onMouseEnter);
    emblaEl?.addEventListener("mouseleave", onMouseLeave);

    startAutoplay();

    return () => {
      stopAutoplay();
      emblaEl?.removeEventListener("mouseenter", onMouseEnter);
      emblaEl?.removeEventListener("mouseleave", onMouseLeave);
    };
  }, [emblaApi]);

  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi]);
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi]);

  useEffect(() => {
    if (!sectionRef.current) return;

    // Check reduced motion preference
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Header reveal only — NOT the carousel track (carousel must be immediately visible)
      gsap.fromTo(
        ".gallery-header-reveal",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.1,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 80%",
            once: true,
          },
        },
      );
    }, sectionRef);

    // Refresh ScrollTrigger after carousel layout settles
    ScrollTrigger.refresh();

    return () => ctx.revert();
  }, []);

  return (
    <section
      id="galeria"
      ref={sectionRef}
      className="section-gradient-warm py-20"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="gallery-header-reveal flex items-end justify-between mb-8">
          <div>
            <p className="text-sm font-black uppercase tracking-[0.2em] text-[#312e8e]/70">
              Confraternidad
            </p>
            <h2 className="mt-2 text-4xl font-black tracking-tight text-[#17214b] sm:text-5xl">
              Todas las generaciones{" "}
              <span className="text-gradient-brand">vuelven a encontrarse</span>
            </h2>
          </div>
          <div className="hidden sm:flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={scrollPrev}
              className="rounded-full"
            >
              <ChevronLeft />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={scrollNext}
              className="rounded-full"
            >
              <ChevronRight />
            </Button>
          </div>
        </div>

        <div className="overflow-hidden" ref={emblaRef}>
          <div className="flex gap-4">
            {IMAGES.map((img, idx) => (
              <figure
                key={idx}
                className="relative flex-[0_0_100%] min-w-0 sm:flex-[0_0_50%] lg:flex-[0_0_33.333%] group"
              >
                <div className="relative aspect-[4/5] overflow-hidden rounded-[1.75rem] shadow-2xl">
                  <img
                    src={img.src}
                    alt={img.label}
                    className="size-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#17214b]/95 to-transparent px-6 pb-6 pt-16">
                    <p className="text-base font-black text-white">
                      {img.label}
                    </p>
                    <p className="mt-1 text-xs text-white/80">{img.caption}</p>
                  </div>
                </div>
              </figure>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
