"use client";

import { AppShell } from "@/components/AppShell";
import { AdminSeccionNav } from "./AdminSeccionNav";

/**
 * Shell of the administration area.
 *
 * It reuses the very same shell as the panel of the team, so the
 * administration area feels like a part of the product and not like a
 * separate application. The only thing it adds is the navigation between the
 * seven sections of the area and the background of the area.
 */
export function AdminShell({ children }: { children: React.ReactNode }) {
  return (
    <AppShell className="surface-page-gradient" title="Administración">
      <AdminSeccionNav />
      {children}
    </AppShell>
  );
}
