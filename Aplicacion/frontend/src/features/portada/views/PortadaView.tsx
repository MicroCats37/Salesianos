import { NavbarBrand } from "@/components/brand/NavbarBrand";
import { ChampionshipSection } from "@/features/portada/components/ChampionshipSection";
import { ExperienceSection } from "@/features/portada/components/ExperienceSection";
import { FamilySection } from "@/features/portada/components/FamilySection";
import { FaqSection } from "@/features/portada/components/FaqSection";
import { FestivalRibbon } from "@/features/portada/components/FestivalRibbon";
import { HeroPortada } from "@/features/portada/components/HeroPortada";
import { MomentosSection } from "@/features/portada/components/MomentosSection";
import { Navbar } from "@/features/portada/components/Navbar";
import { PartySection } from "@/features/portada/components/PartySection";
import { PortadaFooter } from "@/features/portada/components/PortadaFooter";
import { PromotionsSection } from "@/features/portada/components/PromotionsSection";
import { ScheduleSection } from "@/features/portada/components/ScheduleSection";
import { ScrollSnapScope } from "@/features/portada/components/ScrollSnapScope";
import { SponsorsSection } from "@/features/portada/components/SponsorsSection";
import { TiendaSection } from "@/features/portada/components/TiendaSection";
import { VenueSection } from "@/features/portada/components/VenueSection";
import { PartyPassSection } from "../components/PartyPassSection";

/**
 * PortadaView — PUB-01.
 *
 * La portada ES la referencia de la identidad: el escudo, el wordmark, la
 * fecha, la foto a tamaño real y las secciones a pantalla completa con
 * scroll-snap. No se rediseña aquí: se compone lo que ya existe y se le
 * aplica el sistema de tokens.
 *
 * El navbar y el pie son PROPIOS de la portada, por eso la ruta vive en el
 * grupo `(portada)` y no en `(public)`: las demás rutas públicas usan el
 * chrome del shell.
 */
export function PortadaView() {
  return (
    <>
      <ScrollSnapScope />
      <Navbar
        navLinks={[{ href: "/videos", label: "Únete en vivo", live: true }]}
        showActions={false}
        brandSlot={<NavbarBrand showSubtitle={false} />}
      />
      <main id="contenido" className="w-full overflow-x-hidden">
        <HeroPortada />
        <FestivalRibbon />
        <MomentosSection />
        <ExperienceSection />
        <PromotionsSection />
        <PartyPassSection />

        <ChampionshipSection />
        <ScheduleSection />
        <FamilySection />
        <PartySection />
        <TiendaSection />
        <VenueSection />
        <SponsorsSection />
        <FaqSection />
      </main>
      <PortadaFooter />
    </>
  );
}
