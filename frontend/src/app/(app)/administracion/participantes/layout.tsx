import { AdminSeccionGuard } from "@/features/admin/components/AdminSeccionGuard";

/**
 * Server-side guard of the "Participantes" section.
 */
export default async function AdminParticipantesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminSeccionGuard seccionId="participantes">{children}</AdminSeccionGuard>
  );
}
