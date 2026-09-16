import type { ReactNode } from "react";
import { AuthHydrationShell } from "@/features/auth/components";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return <AuthHydrationShell>{children}</AuthHydrationShell>;
}
