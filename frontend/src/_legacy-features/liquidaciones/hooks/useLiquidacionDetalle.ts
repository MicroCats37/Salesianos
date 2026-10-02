"use client";

import { useQuery } from "@tanstack/react-query";

interface UseLiquidacionDetalleOptions {
  id: string;
}

function createPlaceholderHook(name: string) {
  return function useLiquidacionDetalle({ id }: UseLiquidacionDetalleOptions) {
    return useQuery({
      queryKey: [name, id],
      queryFn: async () => {
        // Placeholder - feature not migrated
        await new Promise((r) => setTimeout(r, 100));
        return null;
      },
      enabled: !!id,
    });
  };
}

export const useLiquidacionDetalleEdificacion = createPlaceholderHook(
  "liquidacion-edificacion"
);
export const useLiquidacionDetalleInspeccionObra = createPlaceholderHook(
  "liquidacion-inspeccion-obra"
);
export const useLiquidacionDetalleMecanicaSuelos = createPlaceholderHook(
  "liquidacion-mecanica-suelos"
);
export const useLiquidacionDetalleHabilitacionUrbana = createPlaceholderHook(
  "liquidacion-habilitacion-urbana"
);
export const useLiquidacionDetalleImpactoVial = createPlaceholderHook(
  "liquidacion-impacto-vial"
);
export const useLiquidacionDetalleTaludes = createPlaceholderHook(
  "liquidacion-taludes"
);
