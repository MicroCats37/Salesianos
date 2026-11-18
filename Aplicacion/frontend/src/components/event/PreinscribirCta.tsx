"use client";

import { useRouter } from "next/navigation";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { cn } from "@/lib/utils";

/**
 * Auth-aware CTA pair for the marketing landing pages (home / FestivalBanner
 * + EventFooter).
 *
 * Rules:
 * - If the user is authenticated (Zustand auth store has a user):
 *     - Primary button: → /inscripcion (the wizard, behind the (app) layout)
 *     - Secondary button: → /dashboard (skip the marketing page)
 * - If the user is NOT authenticated:
 *     - Primary button: stash "/inscripcion" in sessionStorage, then /register
 *     - Secondary button: stash "/inscripcion" in sessionStorage, then /login
 *
 * The post-auth destination is picked up by `useRegister` and the
 * `LoginClientShell` login handlers (see POST_AUTH_REDIRECT_KEY), so the URL
 * itself stays clean — no `?nextUrl=…` pollutes the address bar.
 *
 * Why sessionStorage and not a query param:
 *   - Cleaner URLs (no leaked intent in history, no copy-paste noise).
 *   - Tab-scoped: if the user opens /login in a new tab, the redirect intent
 *     does not follow them (they land in /dashboard, the usual landing).
 *   - Survives the OAuth/cookie-set round trip without server round-trips.
 */

export const POST_AUTH_REDIRECT_KEY = "postAuthRedirect";

interface PreinscribirCtaProps {
  className?: string;
}

function stashAndGo(router: ReturnType<typeof useRouter>, path: string, dest: string) {
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem(POST_AUTH_REDIRECT_KEY, dest);
  }
  router.push(path);
}

export function PreinscribirCta({ className }: PreinscribirCtaProps) {
  const user = useAuthUser();
  const router = useRouter();
  const isAuthed = Boolean(user);

  if (isAuthed) {
    return (
      <div className={cn("flex flex-wrap items-center justify-center gap-4", className)}>
        <button
          type="button"
          onClick={() => router.push("/inscripcion")}
          className="rounded-full bg-gradient-to-r from-[#f4c64e] via-[#ec4899] to-[#6366f1] px-10 py-4 text-sm font-black uppercase tracking-widest text-white shadow-2xl shadow-[#ec4899]/30 transition-all hover:scale-105"
        >
          Preinscribir mi equipo
        </button>
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="rounded-full border border-white/30 bg-white/10 px-10 py-4 text-sm font-black uppercase tracking-widest text-white backdrop-blur-sm transition-all hover:bg-white/20"
        >
          Ir a mi panel
        </button>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-wrap items-center justify-center gap-4", className)}>
      <button
        type="button"
        onClick={() => stashAndGo(router, "/register", "/inscripcion")}
        className="rounded-full bg-gradient-to-r from-[#f4c64e] via-[#ec4899] to-[#6366f1] px-10 py-4 text-sm font-black uppercase tracking-widest text-white shadow-2xl shadow-[#ec4899]/30 transition-all hover:scale-105"
      >
        Preinscribir mi equipo
      </button>
      <button
        type="button"
        onClick={() => stashAndGo(router, "/login", "/inscripcion")}
        className="rounded-full border border-white/30 bg-white/10 px-10 py-4 text-sm font-black uppercase tracking-widest text-white backdrop-blur-sm transition-all hover:bg-white/20"
      >
        Ya tengo cuenta
      </button>
    </div>
  );
}
