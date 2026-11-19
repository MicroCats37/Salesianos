"use client";

import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

/**
 * Whether the visitor asked for reduced motion.
 *
 * There is ONE source of truth for this preference: the global rule in
 * `globals.css` disables every animation and transition. This hook exists for
 * the code that must decide something instead of merely looking different —
 * for example a scroll-driven reveal that should not run at all.
 *
 * It is never written per component: the frozen frontend carried two
 * different selector lists that had to be edited by hand for every new
 * animation.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(QUERY);
    const update = () => setReduced(media.matches);

    update();
    media.addEventListener("change", update);

    return () => media.removeEventListener("change", update);
  }, []);

  return reduced;
}
