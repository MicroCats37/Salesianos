import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import type { ReactNode } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthHydrationShell } from "@/features/auth/components";
import { ReactQueryProvider } from "@/providers/ReactQueryProvider";
import { ToastAdapterProvider } from "@/providers/ToastAdapterProvider";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta-sans",
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "Salesianos FEST 2026 — Preinscripción",
  description:
    "Plataforma de preinscripción deportiva — Promoción 2002 / Rumbo a Bodas de Plata",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body
        className={`${jakarta.variable} min-h-screen bg-background text-foreground antialiased font-sans`}
      >
        <ReactQueryProvider>
          <ToastAdapterProvider>
            <AuthHydrationShell>
              <TooltipProvider>{children}</TooltipProvider>
              <Toaster />
            </AuthHydrationShell>
          </ToastAdapterProvider>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
