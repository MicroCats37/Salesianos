"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleTaludesOptions {
  id: string;
}

export function useLiquidacionDetalleTaludes({
  id,
}: UseLiquidacionDetalleTaludesOptions) {
  return useQuery({
    queryKey: ["liquidacion-taludes", id],
    queryFn: async () => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
