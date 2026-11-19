import { ChampionshipSection } from "@/features/portada/components/ChampionshipSection";
import { ClosingSection } from "@/features/portada/components/ClosingSection";
import { ExperienceSection } from "@/features/portada/components/ExperienceSection";
import { FamilySection } from "@/features/portada/components/FamilySection";
import { FaqSection } from "@/features/portada/components/FaqSection";
import { FestivalRibbon } from "@/features/portada/components/FestivalRibbon";
import { HeroPortada } from "@/features/portada/components/HeroPortada";
import { LiveSection } from "@/features/portada/components/LiveSection";
import { MobileTicketBar } from "@/features/portada/components/MobileTicketBar";
import { MomentosSection } from "@/features/portada/components/MomentosSection";
import { Navbar } from "@/features/portada/components/Navbar";
import { NavbarBrand } from "@/components/brand/NavbarBrand";
import { PartyPassSection } from "@/features/portada/components/PartyPassSection";
import { PartySection } from "@/features/portada/components/PartySection";
import { PortadaFooter } from "@/features/portada/components/PortadaFooter";
import { PromotionsSection } from "@/features/portada/components/PromotionsSection";
import { RegistrationSteps } from "@/features/portada/components/RegistrationSteps";
import { ScheduleSection } from "@/features/portada/components/ScheduleSection";
import { ScrollSnapScope } from "@/features/portada/components/ScrollSnapScope";
import { SponsorsSection } from "@/features/portada/components/SponsorsSection";
import { TicketsSection } from "@/features/portada/components/TicketsSection";
import { VenueSection } from "@/features/portada/components/VenueSection";
import { NAV_LINKS } from "@/features/portada/fixtures/festival";

/**
 * PortadaView — PUB-01.
 *
 * La portada ES la referencia de la identidad: el escudo, el wordmark, la
 * fecha, la foto a tamaño real y las secciones a pantalla completa con
 * scroll-snap. No se rediseña aquí: se compone lo que ya existe y se le
 * aplica el sistema de tokens.
 *
 * El navbar y el pie son PROPIOS de la portada (traen su propio ribbon, su
 * CTA de ticket y su barra móvil), por eso la ruta vive en el grupo
 * `(portada)` y no en `(public)`: las demás rutas públicas usan el chrome
 * del shell.
 */
export function PortadaView() {
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
