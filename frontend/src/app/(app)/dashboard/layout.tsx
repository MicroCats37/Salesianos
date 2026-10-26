"use client";

import { AppShell } from "@/components/AppShell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell title="Panel de equipo">{children}</AppShell>;
}
