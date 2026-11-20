import type { ReactNode } from "react";
import { useId } from "react";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface AdminPanelProps {
  /** The name of the block. */
  title: string;
  /** What the block answers. */
  description?: string;
  /** The actions of the block, next to its title. */
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

/**
 * AdminPanel - a block of an administration route.
 *
 * The area is a console: the blocks are separated by the border of the
 * surface, not by a grid of floating cards. A panel has a name, a sentence
 * that says what it answers and its own actions.
 *
 * The depth comes from the surface itself: a gradient that lights the
 * panel from above, a hairline that separates the header from the body and
 * a shadow that lifts the block off the page. The gold rule on top is the
 * gesture of the brand, and it is the ONLY gradient of the block.
 */
export function AdminPanel({
  title,
  description,
  actions,
  children,
  className,
}: AdminPanelProps) {
  const id = useId();

  return (
    <Card
      data-route-block
      className={cn(
        "gap-0 overflow-hidden bg-surface-elevated py-0 shadow-[var(--elevation-sm)] ring-1 ring-foreground/5 transition-shadow duration-(--motion-duration-base) hover:shadow-[var(--elevation-md)]",
        className,
      )}
    >
      <CardHeader className="relative border-b border-border py-4">
        {/*
          La firma de oro: una regla de 2px que acompaña al bloque. Es el
          gesto reconocible del producto, y sólo aparece aquí.
        */}
        <span
          aria-hidden="true"
          className="rule-gold absolute inset-x-0 top-0 h-0.5"
        />
        <CardTitle>
          <h2
            id={id}
            className="font-heading text-base leading-snug font-semibold tracking-tight text-card-foreground"
          >
            {title}
          </h2>
        </CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
        {actions ? <CardAction>{actions}</CardAction> : null}
      </CardHeader>
      <CardContent className="py-4">{children}</CardContent>
    </Card>
  );
}
