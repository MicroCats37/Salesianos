import type { ReactNode } from "react";
import { PortadaSection } from "@/features/portada/components/PortadaSection";

interface FestivalPublicPageProps {
  eyebrow: string;
  title: string[];
  highlighted?: string;
  description: string;
  children: ReactNode;
}

/** Gives public product pages the same visual rhythm as the festival landing. */
export function FestivalPublicPage({
  eyebrow,
  title,
  highlighted,
  description,
  children,
}: FestivalPublicPageProps) {
  return (
    <div className="relative left-1/2 -mx-4 -my-10 w-screen -translate-x-1/2 sm:-mx-6 sm:-my-12 lg:-mx-10">
      <PortadaSection
        eyebrow={eyebrow}
        titulo={title}
        destacado={highlighted}
        copy={description}
        fondo="pagina"
        altura="auto"
      >
        <div className="mt-10 flex flex-col gap-8">{children}</div>
      </PortadaSection>
    </div>
  );
}
