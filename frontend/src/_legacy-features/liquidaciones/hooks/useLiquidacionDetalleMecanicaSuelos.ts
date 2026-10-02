"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleMecanicaSuelosOptions {
  id: string;
}

export function useLiquidacionDetalleMecanicaSuelos({
  id,
}: UseLiquidacionDetalleMecanicaSuelosOptions) {
  return useQuery({
    queryKey: ["liquidacion-mecanica-suelos", id],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
