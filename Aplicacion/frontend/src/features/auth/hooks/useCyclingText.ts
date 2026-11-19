"use client";

import { useEffect, useState } from "react";

// =============================================================================
// CYCLING TEXT — animated keyword in the visual panel headline
// =============================================================================

export interface CyclingEntry {
  word: string;
  article: string;
}

const DEFAULT_LOGIN_WORDS: CyclingEntry[] = [
  { word: "cancha", article: "la" },
  { word: "familia", article: "la" },
  { word: "reencuentro", article: "el" },
  { word: "promocion", article: "la" },
];

const DEFAULT_REGISTER_WORDS: CyclingEntry[] = [
  { word: "inscripcion", article: "tu" },
  { word: "equipo", article: "tu" },
  { word: "delegacion", article: "tu" },
  { word: "ficha", article: "tu" },
];

export function useCyclingText(words?: CyclingEntry[]) {
  const entries =
    words && words.length > 0 ? words : DEFAULT_LOGIN_WORDS;
  const [currentEntry, setCurrentEntry] = useState<CyclingEntry>(entries[0]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setCurrentEntry(entries[0]);
  }, [entries]);

  useEffect(() => {
    if (!mounted) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    let idx = 0;
    let timeoutId: ReturnType<typeof setTimeout>;

    function scheduleNext() {
      timeoutId = setTimeout(() => {
        idx = (idx + 1) % entries.length;
        setCurrentEntry(entries[idx]);
        scheduleNext();
      }, 2800);
    }

    scheduleNext();
    return () => clearTimeout(timeoutId);
  }, [mounted, entries]);

  return { currentEntry, mounted };
}

export const LOGIN_CYCLING_WORDS = DEFAULT_LOGIN_WORDS;
export const REGISTER_CYCLING_WORDS = DEFAULT_REGISTER_WORDS;
