"use client";

import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import ReactQueryProvider from "./ReactQueryProvider";

/**
 * The provider tree of the application.
 *
 * Order is deliberate:
 *
 * 1. `ThemeProvider` sits outermost so the `dark` class reaches `<html>`
 *    before the first paint; `Toaster` reads the theme through `useTheme()`
 *    and needs to live inside it.
 * 2. `QueryClientProvider` wraps everything that consumes server state.
 * 3. `TooltipProvider` is innermost: tooltips are a leaf-level concern and a
 *    delay avoids flickering when the pointer crosses a trigger.
 */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <ReactQueryProvider>
        <TooltipProvider delayDuration={200} skipDelayDuration={300}>
          {children}
        </TooltipProvider>
      </ReactQueryProvider>
    </ThemeProvider>
  );
}
