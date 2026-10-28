import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Acreditaciones" section.
 */
export default async function AdminAcreditacionesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminSeccionGuard seccionId="acreditaciones">{children}</AdminSeccionGuard>
  );
}
