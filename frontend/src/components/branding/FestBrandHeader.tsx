"use client";

import Image, { type ImageProps } from "next/image";
import { cn } from "@/lib/utils";

/**
 * FestBrandHeader — single source of truth for the "Salesianos FEST 2026"
 * brand mark across the frontend.
 *
 * Variants:
 *  - "onLight" (default): logo image on top, dark text. Use on white cards.
 *  - "onDark": logo image on top, light/white text. Use on dark gradient cards.
 *
 * Sizes:
 *  - sm: 64×64 logo + ~1.5rem title. Compact forms (Register, Wizard).
 *  - md: 80×80 logo + ~1.875rem title. Default login.
 *  - lg: 112×112 logo + ~2.25rem title. Marketing-style.
 */
export type FestBrandVariant = "onLight" | "onDark";
export type FestBrandSize = "sm" | "md" | "lg";

export interface FestBrandHeaderProps {
  showLogo?: boolean;
  variant?: FestBrandVariant;
  size?: FestBrandSize;
  /** Optional subtitle displayed below the main mark. */
  subtitle?: string;
  /** Optional label displayed above the mark (eyebrow). */
  eyebrow?: string;
  className?: string;
  imageProps?: Partial<ImageProps>;
}

const SIZE_MAP: Record<FestBrandSize, { logo: number; title: string; ring: string }> = {
  sm: { logo: 64, title: "text-2xl", ring: "border-2" },
  md: { logo: 80, title: "text-3xl sm:text-4xl", ring: "border-2" },
  lg: { logo: 112, title: "text-4xl sm:text-5xl", ring: "border-4" },
};

const LOGO_SRC = "/images/logo.jpeg";

export function FestBrandHeader({
  showLogo = true,
  variant = "onLight",
  size = "md",
  subtitle,
  eyebrow,
  className,
  imageProps,
}: FestBrandHeaderProps) {
  const { logo, title, ring } = SIZE_MAP[size];
  const onDark = variant === "onDark";

  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2",
        onDark ? "text-white" : "text-slate-900",
        className,
      )}
    >
      {eyebrow && (
        <p
          className={cn(
            "text-[10px] font-black uppercase tracking-[0.35em]",
            onDark ? "text-yellow-400" : "text-[#312e8e]",
          )}
        >
          {eyebrow}
        </p>
      )}

      {showLogo && (
        <div
          className={cn(
            "flex items-center justify-center rounded-full p-1 shadow-md",
            ring,
            onDark
              ? "bg-white/10 border-yellow-400/80"
              : "bg-white/40 border-yellow-400",
          )}
          style={{ width: logo, height: logo }}
        >
          <Image
            src={LOGO_SRC}
            alt="Logo Salesianos"
            width={logo}
            height={logo}
            priority
            {...imageProps}
            className={cn(
              "h-auto w-auto rounded-full object-contain",
              imageProps?.className,
            )}
          />
        </div>
      )}

      <h1
        className={cn(
          "font-black tracking-tighter leading-none",
          title,
        )}
        style={{ fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive" }}
      >
        <span
          className="inline-block animate-[goldPulse_2.6s_ease-in-out_infinite] text-yellow-400"
        >
          Salesianos
        </span>{" "}
        <span className="inline-block animate-[cyanPulse_2.6s_ease-in-out_infinite] text-brand-cyan">
          FEST
        </span>{" "}
        <span className={cn(onDark ? "text-white" : "text-slate-900")}>
          2026
        </span>
      </h1>

      {subtitle && (
        <p
          className={cn(
            "text-sm font-medium",
            onDark ? "text-white/80" : "text-slate-600",
          )}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}

export default FestBrandHeader;
