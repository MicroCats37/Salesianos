"use client";

import Image, { type ImageProps } from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * NavbarBrand — compact brand mark for the landing Navbar.
 * Logo (40×40) + inline cursive "Salesianos FEST 2026" with the same
 * Brush Script MT font and brand tokens as `FestBrandHeader`.
 *
 * Fits a 74px Navbar with horizontal nav links to its right.
 */
export interface NavbarBrandProps {
  href?: string;
  showLogo?: boolean;
  showSubtitle?: boolean;
  className?: string;
  imageProps?: Partial<ImageProps>;
}

const LOGO_SRC = "/images/logo.jpeg";

export function NavbarBrand({
  href = "/",
  showLogo = true,
  showSubtitle = true,
  className,
  imageProps,
}: NavbarBrandProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 transition-opacity hover:opacity-90",
        className,
      )}
      aria-label="Salesianos FEST 2026 - Inicio"
    >
      {showLogo && (
        <Image
          src={LOGO_SRC}
          alt="Logo Salesianos"
          width={40}
          height={40}
          priority
          {...imageProps}
          className={cn(
            "size-10 rounded-2xl bg-white object-contain ring-1 ring-[#312e8e]/10",
            imageProps?.className,
          )}
        />
      )}
      <div className="hidden leading-tight sm:block">
        <span
          className="block text-base font-black tracking-[-0.02em] leading-none"
          style={{ fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive" }}
        >
          <span
            className="inline-block animate-[goldPulse_2.6s_ease-in-out_infinite]"
            style={{ color: "var(--brand-cyan-soft)" }}
          >
            Salesianos
          </span>{" "}
          <span className="inline-block animate-[cyanPulse_2.6s_ease-in-out_infinite] text-brand-cyan">
            FEST
          </span>{" "}
          <span className="text-[#17214b]">2026</span>
        </span>
        {showSubtitle && (
          <span className="mt-0.5 block text-[10px] font-bold uppercase tracking-[.16em] text-[#626195]">
            Preinscripcion deportiva
          </span>
        )}
      </div>
    </Link>
  );
}

export default NavbarBrand;
