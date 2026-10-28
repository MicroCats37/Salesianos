import { Suspense } from "react";
import { PaseCompraView } from "@/features/pases";

/**
 * Route of the purchase of the party passes.
 *
 * The page is ROUTING-ONLY: every piece of behaviour lives in the feature
 * (`features/pases`) and the route group `(app)` already guards the session
 * (`app/(app)/layout.tsx`).
 */
export default function PasesPage() {
  return (
    <Suspense fallback={null}>
      <PaseCompraView />
    </Suspense>
  );
}
