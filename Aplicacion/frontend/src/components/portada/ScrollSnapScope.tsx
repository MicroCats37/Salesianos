"use client";

import { useEffect } from "react";

/**
 * Activa el scroll-snap obligatorio SOLO mientras la portada está montada.
 *
 * El contenedor de scroll de la web es el elemento `html`, así que la
 * utilidad se aplica ahí. Se quita al desmontar para no arrastrar el
 * comportamiento al resto de la aplicación (panel, administración, wizard).
 */
export function ScrollSnapScope({ enabled = true }: { enabled?: boolean }) {
  useEffect(() => {
    if (!enabled) return;
    const raiz = document.documentElement;
    // Tailwind v4 separa las dos piezas: `snap-y` fija el eje y
    // `snap-mandatory` fija la estrictez. Hacen falta las dos.
    raiz.classList.add("snap-y", "snap-mandatory");
    return () => raiz.classList.remove("snap-y", "snap-mandatory");
  }, [enabled]);

  return null;
}
