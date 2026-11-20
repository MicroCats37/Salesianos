import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { cn } from "@/lib/utils";

export interface AdminEmptyStateProps {
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
 * AdminEmptyState - the state of an administration block.
 *
 * It is the SAME grammar as the public one (`RouteEmptyState`): the
 * operator and the visitor read the same language, only the tone changes.
 */
export function AdminEmptyState({
  icon,
  title,
  description,
  action,
  className,
}: AdminEmptyStateProps) {
  return (
    <RouteEmptyState
      icon={icon}
      title={title}
      description={description}
      action={action}
      className={cn(className)}
    />
  );
}
