"use client";

import type { ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

export interface AppShellProps {
  /**
   * Content of the area.
   *
   * It arrives through a slot, so a Server Component tree (the pages of the
   * administration area) keeps its own rendering: the client boundary of the
   * shell never drags the pages into the client bundle
   * (`contract/next-app-architecture-contract.md` §3).
   */
  children: ReactNode;
  /** Extra classes of the content area (the background of the area). */
  className?: string;
  /** Title of the mobile bar (optional). */
  title?: string;
}

/**
 * AppShell — the shell of the authenticated area.
 *
 * It is the ONLY place where the sidebar of the product is mounted: the panel
 * of the team (`/dashboard`) and the administration area (`/administracion`)
 * share it, so a change of the shell can never leave one of them behind.
 *
 * The mobile bar is `md:hidden`: from 768px the sidebar is already visible,
 * so the trigger is only needed on a phone. Its hit area is 44px (WCAG 2.5.5)
 * and its accessible name is in Spanish, overriding the English one of the
 * primitive.
 *
 * The horizontal padding does NOT live here: it belongs to the container of
 * every page, because the overview of the administration area is a full-bleed
 * hero and the shell would break it.
 */
export function AppShell({ children, className, title }: AppShellProps) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className={className}>
        <div className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-200 bg-background/95 px-4 backdrop-blur md:hidden">
          <SidebarTrigger aria-label="Abrir menú" className="size-11 -ml-2" />
          {title ? (
            <span className="truncate text-xs font-black uppercase tracking-[0.2em] text-[#17214b]">
              {title}
            </span>
          ) : null}
        </div>
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
