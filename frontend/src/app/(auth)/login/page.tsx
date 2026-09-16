import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginForm } from "@/features/auth/components";

export const metadata: Metadata = {
  title: "Iniciar sesión · Salesianos FEST 2026",
};

export default function LoginPage() {
  return (
    <div className="hero-gradient relative min-h-screen overflow-hidden">
      <div className="hero-gradient-overlay" />
      <div className="absolute -top-20 -right-20 size-80 rounded-full bg-[radial-gradient(circle_at_center,rgba(244,198,78,0.4)_0%,transparent_70%)] blur-3xl animate-orb-float" />
      <div className="absolute -bottom-32 -left-20 size-96 rounded-full bg-[radial-gradient(circle_at_center,rgba(0,189,231,0.3)_0%,transparent_70%)] blur-3xl animate-orb-float-slow" />

      <main className="relative flex min-h-screen items-center justify-center p-4">
        <Suspense fallback={<div className="text-white">Cargando...</div>}>
          <LoginForm />
        </Suspense>
      </main>
    </div>
  );
}
