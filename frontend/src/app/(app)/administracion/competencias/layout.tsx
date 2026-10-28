import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Competencias" section.
 */
export default async function AdminCompetenciasLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminSeccionGuard seccionId="competencias">{children}</AdminSeccionGuard>
  );
}
