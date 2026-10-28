import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Usuarios" section.
 *
 * The caller must hold `admin.usuarios.ver`: reading the accounts table is
 * an operational capability, but MANAGING the accounts is not implemented in
 * this surface.
 */
export default async function AdminUsuariosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AdminSeccionGuard seccionId="usuarios">{children}</AdminSeccionGuard>;
}
