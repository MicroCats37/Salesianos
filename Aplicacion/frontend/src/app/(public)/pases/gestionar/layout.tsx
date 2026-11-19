import Link from "next/link";
import type { ReactNode } from "react";
import { BrandMark } from "@/components/brand/BrandMark";
import { RUTAS } from "@/lib/routes";

/**
 * The chrome of a guest link.
 *
 * A buyer invited to manage a purchase has no session and no account area:
 * the page carries the brand and a way out, nothing else.
 */
export default function GuestLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4 sm:px-6 lg:px-10">
          <Link href={RUTAS.publico.inicio}>
            <BrandMark size={26} />
            <span className="sr-only">Salesianos FEST — Inicio</span>
          </Link>
        </div>
      </header>
      <main
        id="contenido"
        className="mx-auto w-full max-w-[720px] flex-1 px-4 py-10 sm:px-6"
      >
        {children}
      </main>
    </div>
  );
}
