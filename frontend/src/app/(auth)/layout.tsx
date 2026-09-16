import type { ReactNode } from "react";
import { AuthHydrationShell } from "@/features/auth/components";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return <AuthHydrationShell>{children}</AuthHydrationShell>;
}
