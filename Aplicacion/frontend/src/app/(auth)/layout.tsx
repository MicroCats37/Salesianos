import type { ReactNode } from "react";

/**
 * The authentication layout.
 *
 * It is NEUTRAL on purpose: the band of brand and the glass card belong to
 * `AuthShell`, which composes them per variant (login / register). A chrome
 * here would duplicate the panel and the form column.
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-dvh">{children}</div>;
}
