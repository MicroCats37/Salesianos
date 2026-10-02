"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleInspeccionObraOptions {
  id: string;
}

export function useLiquidacionDetalleInspeccionObra({
  id,
}: UseLiquidacionDetalleInspeccionObraOptions) {
  return useQuery({
    queryKey: ["liquidacion-inspeccion-obra", id],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
