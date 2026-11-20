"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type FormSectionHeaderVariant = "soft" | "accent" | "plain";

interface FormSectionHeaderProps {
  title: string;
  icon?: LucideIcon;
  description?: string;
  variant?: FormSectionHeaderVariant;
  count?: number;
  countLabel?: string;
  className?: string;
}

/**
 * Reusable section header for forms.
 * Soft variant avoids the harsh `bg-primary text-primary-foreground` pattern.
 */
export function FormSectionHeader({
  title,
  icon: Icon,
  description,
  variant = "soft",
  count,
  countLabel,
  className,
}: FormSectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 -mx-4 -mt-4 px-4 py-3 rounded-t-xl border-b",
        {
          soft: "bg-primary/10 text-primary border-primary/20",
          accent: "bg-primary text-primary-foreground border-primary",
          plain: "bg-transparent text-foreground border-border",
        }[variant],
        className,
      )}
    >
      {Icon ? <Icon className="size-4 shrink-0" aria-hidden="true" /> : null}
      <h3 className="text-sm font-semibold">{title}</h3>
      {count !== undefined ? (
        <span className="ml-auto text-xs font-medium text-muted-foreground">
          ({count} {countLabel ?? "seleccionado"}
          {count !== 1 ? "s" : ""})
        </span>
      ) : null}
      {description && variant === "plain" ? (
        <p className="ml-2 text-caption text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}
