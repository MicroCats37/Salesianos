"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleImpactoVialOptions {
  id: string;
}

export function useLiquidacionDetalleImpactoVial({
  id,
}: UseLiquidacionDetalleImpactoVialOptions) {
  return useQuery({
    queryKey: ["liquidacion-impacto-vial", id],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
