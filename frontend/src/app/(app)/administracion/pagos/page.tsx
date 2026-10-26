import { Suspense } from "react";
import { AdminPagosLista } from "@/features/admin/components";

/**
 * Operational payments table (A5) with the drilldown of one order (A6).
 */
export default function AdminPagosPage() {
  return (
    <Suspense fallback={null}>
      <AdminPagosLista />
    </Suspense>
  );
}
