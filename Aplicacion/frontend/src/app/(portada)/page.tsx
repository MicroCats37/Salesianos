import type { Metadata } from "next";
import { PortadaView } from "@/features/portada/views/PortadaView";

const title = "Salesianos FEST 2026 · Un festival. Toda la familia.";
const description =
  "Vuelve a encontrarte con tu promoción. Salesianos FEST 2026: deporte, familia y fiesta el 21 de noviembre en la Asociación Okinawense del Perú, Ate, Lima.";

export const metadata: Metadata = {
  title,
  description,
  openGraph: {
    title,
    description,
    type: "website",
    images: ["/images/portada/og-portada.jpg"],
  },
};

/**
 * PUB-01 — La portada.
 *
 * La ruta vive en su propio grupo (`(portada)`) porque trae su propio
 * navbar, su ribbon, su pie y su barra móvil de ticket: son parte de la
 * identidad, no el chrome genérico del shell.
 */
export default function PortadaPage() {
  return <PortadaView />;
}
