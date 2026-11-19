"use client";

import { cn } from "@/lib/utils";

/**
 * AuthGlassCard — la tarjeta de cristal del acceso.
 *
 * El vidrio se compone desde tokens: el fondo sale de `--surface-raised`, el
 * borde de `--surface-raised` y la sombra de `--elevation-lg`. Antes eran
 * `rgba()` sueltos que no tenían pareja en el tema oscuro.
 */
const GLASS_STYLE: React.CSSProperties = {
  background:
    "linear-gradient(160deg, color-mix(in srgb, var(--surface-raised) 96%, transparent) 0%, color-mix(in srgb, var(--surface-raised) 96%, transparent) 100%)",
  border: "1px solid color-mix(in srgb, var(--surface-raised) 65%, transparent)",
  borderRadius: "var(--radius-xl)",
  backdropFilter: "blur(18px)",
  WebkitBackdropFilter: "blur(18px)",
  boxShadow: "var(--elevation-lg)",
  color: "var(--foreground)",
};

export interface AuthGlassCardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function AuthGlassCard({
  children,
  className = "",
  style,
}: AuthGlassCardProps) {
  return (
    <div
      className={cn(
        "auth-glass-card text-foreground p-6 sm:p-8",
        className,
      )}
      style={{ ...GLASS_STYLE, ...style }}
    >
      {children}
    </div>
  );
}
