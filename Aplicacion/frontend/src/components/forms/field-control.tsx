import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export const FIELD_ICON_PADDING = "pl-10";

export interface FieldIconProps {
  icon: LucideIcon;
  invalid?: boolean;
}

export function FieldIcon({ icon: Icon, invalid = false }: FieldIconProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute left-3 top-1/2 -translate-y-1/2",
        invalid ? "text-destructive" : "text-muted-foreground",
      )}
    >
      <Icon className="size-4" />
    </span>
  );
}
