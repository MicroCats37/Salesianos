import type { Metadata } from "next";
import { ResponsableDashboardView } from "@/features/inscripcion/views/ResponsableDashboardView";

export const metadata: Metadata = {
  title: "Mi inscripción · Salesianos FEST 2026",
};

export default function DashboardPage() {
  return <ResponsableDashboardView />;
}
