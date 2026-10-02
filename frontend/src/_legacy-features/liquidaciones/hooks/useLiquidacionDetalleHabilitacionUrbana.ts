"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleHabilitacionUrbanaOptions {
  id: string;
}

export function useLiquidacionDetalleHabilitacionUrbana({
  id,
}: UseLiquidacionDetalleHabilitacionUrbanaOptions) {
  return useQuery({
    queryKey: ["liquidacion-habilitacion-urbana", id],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
