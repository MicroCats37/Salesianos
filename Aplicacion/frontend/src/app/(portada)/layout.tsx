import type { ReactNode } from "react";
import { RouteTransition } from "@/components/shell/RouteTransition";

/**
 * The layout of the portada.
 *
 * The portada is the only route WITHOUT a layout of its own chrome, and it
 * is the one route that had no transition at all: it lives in the root
 * layout, so it never went through the shared transition.
 *
 * This layout gives it the same treatment as the other families: the
 * content enters with the shared fade and every navigation inside the
 * product arrives with the shared GSAP timeline.
 */
export default function PortadaLayout({ children }: { children: ReactNode }) {
  return <RouteTransition>{children}</RouteTransition>;
}
