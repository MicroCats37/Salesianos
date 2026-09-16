"use client";

import { create } from "zustand";

/**
 * UI State for the Libro de Reclamaciones stepper form.
 *
 * Owns ephemeral modal/open state, currentStep tracking, the aggregated
 * form data across steps, and the isSubmitting flag.
 *
 * Does NOT own server data — no TanStack Query, no API calls.
 */
interface LibroReclamacionesUIState {
  /** Whether the stepper modal is open */
  isOpen: boolean;
  /** Current step index (0-based) */
  currentStep: number;
  /** Aggregated data from all completed steps */
  aggregate: Record<string, unknown>;
  /** Whether the final submit is in flight */
  isSubmitting: boolean;
  /** Whether the submit succeeded (shows confirmation state) */
  isSubmitted: boolean;
  /** Open the stepper modal */
  open: () => void;
  /** Close the stepper modal and reset state */
  close: () => void;
  /** Navigate to a specific step */
  goToStep: (step: number) => void;
  /** Update the aggregated form data */
  setAggregate: (data: Record<string, unknown>) => void;
  /** Set submit in-flight flag */
  setSubmitting: (val: boolean) => void;
  /** Mark as successfully submitted */
  setSubmitted: (val: boolean) => void;
  /** Full reset to initial state */
  reset: () => void;
}

const INITIAL_STATE = {
  isOpen: false,
  currentStep: 0,
  aggregate: {},
  isSubmitting: false,
  isSubmitted: false,
};

export const useLibroReclamacionesUIStore = create<LibroReclamacionesUIState>(
  (set) => ({
    ...INITIAL_STATE,

    open: () => set({ isOpen: true }),

    close: () => set({ ...INITIAL_STATE }),

    goToStep: (step) => set({ currentStep: step }),

    setAggregate: (data) => set({ aggregate: data }),

    setSubmitting: (val) => set({ isSubmitting: val }),

    setSubmitted: (val) => set({ isSubmitted: val }),

    reset: () => set({ ...INITIAL_STATE }),
  }),
);
