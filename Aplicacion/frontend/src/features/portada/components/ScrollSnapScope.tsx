"use client";

import { useEffect } from "react";

/**
 * Activa el scroll-snap SOLO mientras la portada está montada.
 *
 * El contenedor de scroll de la web es el elemento `html`, así que la
 * utilidad se aplica ahí. Se quita al desmontar para no arrastrar el
 * comportamiento al resto de la aplicación (panel, administración, wizard).
 *
 * La estrictez es `proximity`, no `mandatory`: una sección que crece más que
 * la pantalla (el hero con mucho contenido, un viewport bajo) deja de tener
 * un punto de anclaje válido y, con `mandatory`, el scroll queda SECESTRADO:
 * el visitante no puede desplazarse dentro de la sección. `proximity` mantiene
 * la sensación de avance sección a sección cuando la sección sí cabe, y
 * devuelve el control al visitante cuando no cabe.
 */
export function ScrollSnapScope({ enabled = true }: { enabled?: boolean }) {
  useEffect(() => {
    if (!enabled) return;
    const raiz = document.documentElement;
    // Tailwind v4 separa las dos piezas: `snap-y` fija el eje y
    // `snap-proximity` fija la estrictez. Hacen falta las dos.
    raiz.classList.add("snap-y", "snap-proximity");
    return () => raiz.classList.remove("snap-y", "snap-proximity");
  }, [enabled]);

  return null;
}
