import { ImageOff } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LogoPatrocinador as Logo } from "../types/patrocinador.types";

export interface LogoPatrocinadorProps {
  /** The logo of identity, or `null` when the sponsor has none. */
  logo: Logo | null;
  /** The name of the sponsor: it is the alternative text of the logo. */
  nombre: string;
  className?: string;
}

/**
 * LogoPatrocinador - the logo of identity of a sponsor.
 *
 * The presenter publishes whether the file is READABLE, because a stored
 * file can be missing on disk. The gap is shown as a gap: the interface
 * never draws a broken image and never pretends that the logo exists.
 *
 * The alternative text is the NAME of the sponsor, so the logo never
 * repeats a caption that the surrounding markup already says.
 */
export function LogoPatrocinador({
  logo,
  nombre,
  className,
}: LogoPatrocinadorProps) {
  if (!logo) {
    return (
      <span
        className={cn(
          "flex aspect-square w-16 items-center justify-center rounded-[var(--radius-md)] border border-dashed border-border bg-surface-recessed text-muted-foreground",
          className,
        )}
      >
        <ImageOff className="size-5" aria-hidden="true" />
        <span className="sr-only">{`${nombre} no tiene logo`}</span>
      </span>
    );
  }

  if (!logo.disponible || !logo.url) {
    return (
      <span
        className={cn(
          "flex aspect-square w-16 flex-col items-center justify-center gap-1 rounded-[var(--radius-md)] border border-dashed border-border bg-surface-recessed text-muted-foreground",
          className,
        )}
      >
        <ImageOff className="size-5" aria-hidden="true" />
        <span className="sr-only">{`El logo de ${nombre} no está disponible`}</span>
      </span>
    );
  }

  return (
    <img
      src={logo.url}
      alt={`Logo de ${nombre}`}
      className={cn(
        "aspect-square w-16 rounded-[var(--radius-md)] border border-border bg-surface-raised object-contain p-1",
        className,
      )}
    />
  );
}
