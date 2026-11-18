"use client";

import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * NavbarBrand — compact "Salesianos FEST" wordmark image for the landing
 * Navbar. Sized to fit a 74px Navbar with horizontal nav links to its right.
 *
 * Wordmark switch:
 *  - "brand2" (default): navy/cyan wordmark.
 *  - "brand": cyan wordmark.
 */
export type NavbarBrandWordmark = "brand" | "brand2";

export interface NavbarBrandProps {
  href?: string;
  showLogo?: boolean;
  showSubtitle?: boolean;
  wordmark?: NavbarBrandWordmark;
  className?: string;
}

const WORDMARK_SRC: Record<NavbarBrandWordmark, string> = {
  brand: "/images/brand.png",
  brand2: "/images/brand2.png",
};

export function NavbarBrand({
  href = "/",
  showLogo = true,
  showSubtitle = true,
  wordmark = "brand2",
  className,
}: NavbarBrandProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 transition-opacity hover:opacity-90",
        className,
      )}
      aria-label="Salesianos FEST - Inicio"
    >
      {showLogo && (
        <Image
          src={WORDMARK_SRC[wordmark]}
          alt="Salesianos FEST"
          width={350}
          height={105}
          priority
          style={{ height: 32, width: "auto" }}
          className="select-none"
        />
      )}
      {showSubtitle && (
        <span className="hidden text-[10px] font-bold uppercase tracking-[.16em] text-[#626195] sm:block">
          Preinscripcion deportiva
        </span>
      )}
    </Link>
  );
}

export default NavbarBrand;
