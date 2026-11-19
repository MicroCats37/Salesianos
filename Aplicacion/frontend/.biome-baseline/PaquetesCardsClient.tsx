"use client";

import type { Paquete } from "@/features/landing/paquetes.service";
import { PaquetesCards } from "./PaquetesCards";

interface PaquetesCardsClientProps {
  paquetes: Paquete[];
}

export function PaquetesCardsClient({ paquetes }: PaquetesCardsClientProps) {
  return <PaquetesCards paquetes={paquetes} />;
}
