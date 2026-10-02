"use client";

import { cn } from "@/lib/utils";

const GLASS_STYLE: React.CSSProperties = {
  background:
    "linear-gradient(160deg, rgba(255,255,255,0.96) 0%, rgba(248,250,255,0.96) 50%, rgba(241,245,253,0.96) 100%)",
  border: "1px solid rgba(255,255,255,0.65)",
  borderRadius: "1.75rem",
  backdropFilter: "blur(18px)",
  WebkitBackdropFilter: "blur(18px)",
  boxShadow:
    "0 32px 90px rgba(7,8,28,0.45), 0 2px 0 rgba(255,255,255,0.55) inset",
  color: "var(--brand-deep-navy)",
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
        "auth-glass-card text-brand-deep-navy p-6 sm:p-8",
        className,
      )}
      style={{ ...GLASS_STYLE, ...style }}
    >
      {children}
    </div>
  );
}

