import { Suspense } from "react";
import { AdminParticipantesLista } from "@/features/admin/components";

/**
 * Registered people (A8) and roster rows (A9) — two tabs, two namespaces.
 */
export default function AdminParticipantesPage() {
  return (
    <Suspense fallback={null}>
      <AdminParticipantesLista />
    </Suspense>
  );
}
