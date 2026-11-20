"use client";

import { gsap } from "gsap";
import type { RefObject } from "react";
import { useEffect, useLayoutEffect, useRef } from "react";

/**
 * `useLayoutEffect` in the browser, `useEffect` in the server.
 *
 * The animation must be armed BEFORE the browser paints, otherwise the
 * content appears at its final position and the transition reads as a flicker.
 */
const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;

/** The element the selector text of the animations is resolved against. */
export type UseGSAPScope =
  | RefObject<HTMLElement | null>
  | HTMLElement
  | null
  | undefined;

export interface UseGSAPOptions {
  /**
   * The scope of the animations.
   *
   * A REF is the recommended form: the element only exists after the first
   * render, and a ref is the only honest way to point at it. Selectors used
   * inside the setup are then resolved inside that element and nowhere else.
   */
  scope?: UseGSAPScope;
  /**
   * The dependencies that re-run the setup.
   *
   * When a dependency changes, the previous context is REVERTED before the new
   * setup runs: the animations of the previous state die and their inline
   * styles are removed.
   */
  dependencies?: readonly unknown[];
}

/**
 * `useGSAP` - run a GSAP setup inside an automatic scope.
 *
 * It is the contract of `@gsap/react`'s `useGSAP`, implemented over the
 * `gsap` package this project already depends on:
 *
 * - the setup runs inside a `gsap.context()`, so every selector text is
 *   resolved against the scoped element and never leaks into the page;
 * - the context is REVERTED when the component unmounts and when a
 *   dependency changes, so a tween can never outlive its route;
 * - the setup may RETURN a cleanup function, which runs on that same revert.
 *
 * The `contextSafe` helper of the original package is not needed here: this
 * project never creates a tween from an event handler that runs after the
 * setup finished.
 */
export function useGSAP(
  setup: () => void | (() => void),
  { scope, dependencies = [] }: UseGSAPOptions = {},
): void {
  const setupRef = useRef(setup);
  setupRef.current = setup;

  const scopeRef = useRef(scope);
  scopeRef.current = scope;

  useIsomorphicLayoutEffect(() => {
    const raw = scopeRef.current;
    const element =
      raw && typeof raw === "object" && "current" in raw
        ? raw.current
        : (raw as HTMLElement | null);

    const context = gsap.context(() => {
      setupRef.current();
    }, element ?? undefined);

    return () => {
      context.revert();
    };
    // The dependency list is owned by the caller: it must keep the same
    // length between renders, exactly like `useEffect`.
  }, dependencies);
}
