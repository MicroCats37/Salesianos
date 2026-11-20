import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { cn } from "@/lib/utils";

export interface RouteEmptyStateProps {
  /** The icon that names the kind of state. */
  icon: LucideIcon;
  /** What does not exist. */
  title: string;
  /** Why it does not exist and what happens when it does. */
  description: ReactNode;
  /** The action that resolves the state. */
  action?: ReactNode;
  className?: string;
}

/**
 * RouteEmptyState - the state of a block that has nothing to show.
 *
 * It says WHAT does not exist, WHY, and what will happen when it exists.
 * It never invents a figure to fill the space: an empty area is
 * information, not a failure of the design.
 */
export function RouteEmptyState({
  icon: Icono,
  title,
  description,
  action,
  className,
}: RouteEmptyStateProps) {
  return (
    <Empty
      className={cn(
        "border border-border bg-surface-recessed/60 shadow-[var(--elevation-sm)]",
        className,
      )}
    >
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icono className="size-5" aria-hidden="true" />
        </EmptyMedia>
        <EmptyTitle className="text-base">{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      {action ? <EmptyContent>{action}</EmptyContent> : null}
    </Empty>
  );
}
