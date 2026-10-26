import { Suspense } from "react";
import { AdminAcreditacionesLista } from "@/features/admin/components";

/**
 * Accreditations (A10, A11) and access log (A12) — two tabs, two namespaces.
 */
export default function AdminAcreditacionesPage() {
  return (
    <Suspense fallback={null}>
      <AdminAcreditacionesLista />
    </Suspense>
  );
}
