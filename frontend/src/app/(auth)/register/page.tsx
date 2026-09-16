import type { Metadata } from "next";
import { RegisterForm } from "@/features/auth/components";

export const metadata: Metadata = {
  title: "Crear cuenta · Salesianos FEST 2026",
};

export default function RegisterPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#f4c64e] via-[#ffd97a] to-[#f4c64e]">
      <div className="absolute -top-20 -right-20 size-80 rounded-full bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.3)_0%,transparent_70%)] blur-3xl animate-orb-float" />
      <div className="absolute -bottom-32 -left-20 size-96 rounded-full bg-[radial-gradient(circle_at_center,rgba(49,46,142,0.3)_0%,transparent_70%)] blur-3xl animate-orb-float-slow" />

      <main className="relative flex min-h-screen items-center justify-center p-4">
        <RegisterForm />
      </main>
    </div>
  );
}
