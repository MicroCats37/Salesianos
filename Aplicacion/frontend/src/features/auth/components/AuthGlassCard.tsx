"use client";

import { cn } from "@/lib/utils";

/**
 * AuthGlassCard — la tarjeta de cristal del acceso.
 *
 * El vidrio se compone desde tokens: el fondo sale de `--surface-raised`, el
 * borde de `--border` y la sombra de `--elevation-lg`. Antes eran colores
 * sueltos que no tenían pareja en el tema oscuro.
 *
 * El borde es un ROL y no un tono del propio relleno: un borde del mismo
 * color que la tarjeta no la separa del gradiente profundo que hay detrás.
 */
const GLASS_STYLE: React.CSSProperties = {
  background:
    "linear-gradient(160deg, color-mix(in srgb, var(--surface-raised) 96%, transparent) 0%, color-mix(in srgb, var(--surface-raised) 96%, transparent) 100%)",
  border: "1px solid var(--border)",
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
      className={cn("text-foreground p-6 sm:p-8", className)}
      style={{ ...GLASS_STYLE, ...style }}
    >
      {children}
    </div>
  );
}
