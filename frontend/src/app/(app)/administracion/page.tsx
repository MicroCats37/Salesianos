import { AdminOverview } from "@/features/admin/components";

/**
 * Operational overview of the active event (A1).
 *
 * The page is a thin composition: the guard lives in the layout and every
 * metric is fetched and rendered by the administration feature.
 */
export default function AdministracionPage() {
  return <AdminOverview />;
}
