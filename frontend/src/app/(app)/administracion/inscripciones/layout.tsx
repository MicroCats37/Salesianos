import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Inscripciones" section.
 *
 * The caller must hold the capability of the section (the operational staff
 * and the break-glass tier). A direct URL never reaches a section the
 * caller may not open.
 */
export default async function AdminInscripcionesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminSeccionGuard seccionId="inscripciones">{children}</AdminSeccionGuard>
  );
}
