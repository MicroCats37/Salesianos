import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Equipos" section.
 */
export default async function AdminEquiposLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AdminSeccionGuard seccionId="equipos">{children}</AdminSeccionGuard>;
}
