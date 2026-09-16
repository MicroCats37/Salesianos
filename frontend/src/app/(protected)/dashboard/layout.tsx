import type { ReactNode } from "react";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ResponsableSidebar } from "@/components-app/sidebar";
import { requireRole } from "@/lib/auth/require-role";

export default async function ResponsableLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requireRole("responsable");

  return (
    <SidebarProvider>
      <ResponsableSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <span className="text-sm font-bold text-[#17214b] group-data-[collapsible=icon]:hidden">
            Salesianos FEST 2026 · Mi inscripción
          </span>
        </header>
        <div className="p-4 lg:p-6">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
