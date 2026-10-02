"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleEdificacionOptions {
  id: string;
}

export function useLiquidacionDetalleEdificacion({ id }: UseLiquidacionDetalleEdificacionOptions) {
  return useQuery({
    queryKey: ["liquidacion-edificacion", id],
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    queryFn: async (): Promise<any> => {
      await new Promise((r) => setTimeout(r, 100));
      return null;
    },
    enabled: !!id,
  });
}
