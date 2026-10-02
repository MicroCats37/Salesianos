import { redirect } from "next/navigation";
import { getUserSession } from "@/lib/auth";

/**
 * Server Component layout for the (app) route group.
 *
 * Redirects unauthenticated users to the public home page ("/") so the
 * visitor lands on marketing content with explicit CTA links instead of
 * being forced to /login. The proxy + Navbar provide the entry points.
 */
export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getUserSession();

  if (!user) {
    redirect("/");
  }

  return <>{children}</>;
}
