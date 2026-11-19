"use client";

import type { Paquete } from "@/features/portada/fixtures/paquetes.fixture";
import { PaquetesCards } from "./PaquetesCards";

interface PaquetesCardsClientProps {
  paquetes: Paquete[];
}

export function PaquetesCardsClient({ paquetes }: PaquetesCardsClientProps) {
  return <PaquetesCards paquetes={paquetes} />;
}
