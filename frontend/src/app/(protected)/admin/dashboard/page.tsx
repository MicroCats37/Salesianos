import type { Metadata } from "next";
import { AdminDashboardStats } from "@/features/admin/inscripciones/components/AdminDashboardStats";
import { requireRole } from "@/lib/auth/require-role";

export const metadata: Metadata = {
  title: "Dashboard Comité · Salesianos FEST 2026",
};

export default async function AdminDashboardPage() {
  await requireRole("admin_comite", "admin_finanzas");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-[#17214b]">
          Dashboard del Comité
        </h1>
        <p className="mt-1 text-muted-foreground">
          Resumen de las inscripciones de Salesianos FEST 2026.
        </p>
      </div>
      <AdminDashboardStats />
    </div>
  );
}
