import Image, { type ImageProps } from "next/image";
import { cn } from "@/lib/utils";

/**
 * FestBrandHeader — single source of truth for the "Salesianos FEST" brand
 * mark across the frontend. Renders the circular logo and the horizontal
 * wordmark image together.
 *
 * Variants:
 *  - "onLight" (default): light card background.
 *  - "onDark": dark gradient background (light subtitle).
 *
 * Wordmark switch:
 *  - "brand2" (default): navy/cyan wordmark for login, register, wizard,
 *    navbar, footer and any non-landing context.
 *  - "brand": cyan wordmark for the marketing landing banner only.
 *
 * Sizes:
 *  - sm: compact forms (Register, Wizard).
 *  - md: default login.
 *  - lg: marketing-style.
 */
export type FestBrandVariant = "onLight" | "onDark";
export type FestBrandSize = "sm" | "md" | "lg";
export type FestBrandWordmark = "brand" | "brand2";

export interface FestBrandHeaderProps {
  showLogo?: boolean;
  variant?: FestBrandVariant;
  size?: FestBrandSize;
  wordmark?: FestBrandWordmark;
  /** Optional subtitle displayed below the main mark. */
  subtitle?: string;
  /** Optional label displayed above the mark (eyebrow). */
  eyebrow?: string;
  className?: string;
  imageProps?: Partial<ImageProps>;
}

const SIZE_MAP: Record<FestBrandSize, { logo: number; wordmark: number }> = {
  sm: { logo: 56, wordmark: 40 },
  md: { logo: 72, wordmark: 56 },
  lg: { logo: 128, wordmark: 192 },
};

const LOGO_SRC = "/images/logo.jpeg";
const WORDMARK_SRC: Record<FestBrandWordmark, string> = {
  brand: "/images/brand.png",
  brand2: "/images/brand2.png",
};

export function FestBrandHeader({
  showLogo = true,
  variant = "onLight",
  size = "md",
  wordmark = "brand2",
  subtitle,
  eyebrow,
  className,
  imageProps,
}: FestBrandHeaderProps) {
  const { logo, wordmark: wordmarkHeight } = SIZE_MAP[size];
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
            "flex items-center justify-center rounded-full p-1 shadow-md ring-2 ring-yellow-400",
            onDark ? "bg-white/10" : "bg-white/40",
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

      <Image
        src={WORDMARK_SRC[wordmark]}
        alt="Salesianos FEST"
        width={400}
        height={120}
        priority
        style={{ height: wordmarkHeight, width: "auto" }}
        className="select-none"
      />

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
