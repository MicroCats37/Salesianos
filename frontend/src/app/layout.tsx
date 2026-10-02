import type { Metadata } from "next";
import { Geist_Mono, Plus_Jakarta_Sans } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import Providers from "@/providers/ReactQueryProvider";

/**
 * Izipay Web Core 2.0 SDK — loaded once, before page becomes interactive.
 * The URL is configurable via NEXT_PUBLIC_IZIPAY_SDK_URL.
 * Only public key allowed in frontend env; secrets stay in Django settings.
 * Disabled when NEXT_PUBLIC_IZIPAY_ENABLED !== "true".
 */
const IZIPAY_SDK_URL =
  process.env.NEXT_PUBLIC_IZIPAY_SDK_URL ||
  "https://sandbox-checkout.izipay.pe/payments/v1/js/index.js";

const isIzipayEnabled =
  process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta-sans",
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700", "800"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CAM",
  description: "CAM",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${plusJakartaSans.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        {isIzipayEnabled && (
          <Script src={IZIPAY_SDK_URL} strategy="beforeInteractive" />
        )}
      </head>
      <body className="h-full antialiased" suppressHydrationWarning>
        <Providers>
          <TooltipProvider>{children}</TooltipProvider>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
