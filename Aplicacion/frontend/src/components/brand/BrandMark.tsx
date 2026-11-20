import Image from "next/image";
import { cn } from "@/lib/utils";

/**
 * BrandMark - the single source of truth for the "Salesianos FEST" mark.
 *
 * It renders the official crest and the wordmark side by side. Both are
 * real assets: the crest is the circular `logo.jpeg` and the wordmark is
 * `brand2.png` (navy/cyan), the variant that reads on light surfaces.
 *
 * Every colour comes from a token - the mark never carries a literal.
 */
export interface BrandMarkProps {
  /** Height of the wordmark in pixels. */
  size?: number;
  /** Render the crest next to the wordmark. */
  withCrest?: boolean;
  /** Render the wordmark in its cyan variant (marketing surfaces). */
  wordmark?: "brand" | "brand2";
  className?: string;
}

const LOGO_SRC = "/images/logo.jpeg";
const WORDMARK_SRC = {
  brand: "/images/brand.png",
  brand2: "/images/brand2.png",
} as const;

export function BrandMark({
  size = 28,
  withCrest = false,
  wordmark = "brand2",
  className,
}: BrandMarkProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      {withCrest ? (
        <Image
          src={LOGO_SRC}
          alt=""
          width={size + 8}
          height={size + 8}
          className="size-[var(--brand-crest)] rounded-full object-contain ring-2 ring-accent/70"
          style={{ "--brand-crest": `${size + 8}px` } as React.CSSProperties}
        />
      ) : null}
      <Image
        src={WORDMARK_SRC[wordmark]}
        alt="Salesianos FEST"
        width={size * 3}
        height={size}
        priority
        style={{ height: size, width: "auto" }}
        className="select-none"
      />
    </span>
  );
}
