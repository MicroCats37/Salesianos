import { redirect } from "next/navigation";
import type { UserRole } from "@/infra/drizzle/schema";
import { getSession } from "./get-session";

export async function requireRole(...allowedRoles: UserRole[]) {
  const session = await getSession();

  if (!session) {
    redirect("/login");
  }

  if (!allowedRoles.includes(session.rol as UserRole)) {
    if (session.rol === "admin_comite" || session.rol === "admin_finanzas") {
      redirect("/admin/comite/inscripciones");
    } else {
      redirect("/dashboard");
    }
  }

  return session;
}
