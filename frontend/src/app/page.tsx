import type { Metadata } from "next";
import { NavbarBrand } from "@/components/branding/NavbarBrand";
import { Navbar } from "@/components/landing/Navbar";
import { ChampionshipSection } from "@/components/portada/ChampionshipSection";
import { ClosingSection } from "@/components/portada/ClosingSection";
import { ExperienceSection } from "@/components/portada/ExperienceSection";
import { FamilySection } from "@/components/portada/FamilySection";
import { FaqSection } from "@/components/portada/FaqSection";
import { FestivalRibbon } from "@/components/portada/FestivalRibbon";
import { HeroPortada } from "@/components/portada/HeroPortada";
import { LiveSection } from "@/components/portada/LiveSection";
import { MobileTicketBar } from "@/components/portada/MobileTicketBar";
import { MomentosSection } from "@/components/portada/MomentosSection";
import { PartyPassSection } from "@/components/portada/PartyPassSection";
import { PartySection } from "@/components/portada/PartySection";
import { PortadaFooter } from "@/components/portada/PortadaFooter";
import { PromotionsSection } from "@/components/portada/PromotionsSection";
import { RegistrationSteps } from "@/components/portada/RegistrationSteps";
import { ScheduleSection } from "@/components/portada/ScheduleSection";
import { ScrollSnapScope } from "@/components/portada/ScrollSnapScope";
import { SponsorsSection } from "@/components/portada/SponsorsSection";
import { TicketsSection } from "@/components/portada/TicketsSection";
import { VenueSection } from "@/components/portada/VenueSection";
import { NAV_LINKS } from "@/features/portada/config/festival";

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

export default function PortadaPage() {
  return (
    <>
      <ScrollSnapScope />
      <Navbar
        navLinks={[...NAV_LINKS]}
        brandSlot={<NavbarBrand showSubtitle={false} />}
      />
      <main id="contenido" className="w-full overflow-x-hidden pb-20 lg:pb-0">
        <HeroPortada />
        <FestivalRibbon />
        <MomentosSection />
        <ExperienceSection />
        <PromotionsSection />
        <ChampionshipSection />
        <ScheduleSection />
        <FamilySection />
        <PartySection />
        <TicketsSection />
        <PartyPassSection />
        <RegistrationSteps />
        <LiveSection />
        <VenueSection />
        <SponsorsSection />
        <FaqSection />
        <ClosingSection />
      </main>
      <PortadaFooter />
      <MobileTicketBar />
    </>
  );
}
