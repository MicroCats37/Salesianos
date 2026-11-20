"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { RUTAS } from "@/lib/routes";

/**
 * Auth-aware preinscribir CTA used by landing paquete cards.
 * Client component — uses useAuthUser() which requires a client context.
 */
export function PreinscribirCTA() {
  const user = useAuthUser();

  return (
    <div className="mt-auto">
      <Button
        asChild
        className="btn-brand-gradient btn-shine w-full justify-center rounded-2xl h-12 text-sm font-black"
      >
        <Link href={user ? RUTAS.cuenta.inscripcion : RUTAS.auth.registro}>
          Preinscribir equipo
        </Link>
      </Button>
    </div>
  );
}
