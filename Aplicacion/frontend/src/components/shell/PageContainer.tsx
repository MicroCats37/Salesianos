import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * PageContainer - the ONE container of the public area.
 *
 * `ui-ux-pro-max` (Layout, Container Width): "Don't let text span full
 * viewport width" — the measure stays at 65-75 characters and the content
 * never touches the edge of the viewport.
 *
 * The container belongs to the PAGE, not to `<main>`: a marketing section may
 * leave the container to run full bleed (a hero, a photo band). A section
 * that leaves it says so with `bleed`, and the rest inherits the measure.
 */
export interface PageContainerProps {
  children: ReactNode;
  /** Run the content edge to edge, without the container. */
  bleed?: boolean;
  /** Vertical rhythm of the container. */
  spacing?: "none" | "tight" | "normal";
  className?: string;
}

const SPACING = {
  none: "",
  tight: "py-8",
  normal: "py-12 sm:py-16",
} as const;

export function PageContainer({
  children,
  bleed = false,
  spacing = "normal",
  className,
}: PageContainerProps) {
  if (bleed) {
    return <div className={cn(className)}>{children}</div>;
  }

  return (
    <div
      className={cn(
        "mx-auto w-full max-w-[1200px] px-4 sm:px-6 lg:px-10",
        SPACING[spacing],
        className,
      )}
    >
      {children}
    </div>
  );
}
