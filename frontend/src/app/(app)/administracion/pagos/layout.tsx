import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Pagos" section.
 *
 * The caller must hold `admin.pagos.ver`: the operational staff READS the
 * payments. Approving or annulling them is a separate, sensitive capability
 * (`admin.pagos.aprobar`) that the backend evaluates on every call.
 */
export default async function AdminPagosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AdminSeccionGuard seccionId="pagos">{children}</AdminSeccionGuard>;
}
