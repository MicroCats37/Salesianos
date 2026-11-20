import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

/**
 * The automatic cleanup of the testing library is registered only when the
 * globals of the runner are enabled. This project does NOT enable them, so
 * the cleanup is explicit: a suite never sees the DOM of the previous one.
 */
afterEach(() => {
  cleanup();
});

/**
 * Setup of the component suites of the frontend.
 *
 * The suite of this file lives in `jsdom` (the environment is declared per
 * file with `// @vitest-environment jsdom`) and it needs three families of
 * shims that jsdom does not implement:
 *
 * 1. The observers that the floating layers of Radix (the `Select` of the
 *    shared form) use to measure their content.
 * 2. The pointer capture API that Radix asks for when the pointer is
 *    released outside of a layer.
 * 3. `scrollIntoView`, that jsdom does not implement and that the dialogs
 *    call when they open.
 * 4. `IntersectionObserver`, that jsdom does not implement either and that
 *    the anchor index of the information page uses to mark the section that
 *    is on screen.
 *
 * The shims are MINIMAL: they only satisfy the contract of the API, they
 * never simulate a behaviour.
 */

if (typeof globalThis.ResizeObserver === "undefined") {
  class ResizeObserverShim implements ResizeObserver {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }

  globalThis.ResizeObserver = ResizeObserverShim;
}

if (typeof globalThis.IntersectionObserver === "undefined") {
  class IntersectionObserverShim implements IntersectionObserver {
    readonly root: Element | Document | null = null;
    readonly rootMargin: string = "0px";
    readonly thresholds: ReadonlyArray<number> = [];

    constructor(
      _callback: IntersectionObserverCallback,
      options?: IntersectionObserverInit,
    ) {
      this.root = (options?.root as Element | Document | null) ?? null;
      this.rootMargin = options?.rootMargin ?? "0px";
      this.thresholds = Array.isArray(options?.threshold)
        ? options.threshold
        : [options?.threshold ?? 0];
    }

    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
    takeRecords(): IntersectionObserverEntry[] {
      return [];
    }
  }

  globalThis.IntersectionObserver =
    IntersectionObserverShim as unknown as typeof IntersectionObserver;
}

if (typeof Element !== "undefined") {
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
  }
  if (!Element.prototype.setPointerCapture) {
    Element.prototype.setPointerCapture = () => {};
  }
  if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => {};
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
}

if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = ((consulta: string) => ({
    matches: false,
    media: consulta,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as typeof window.matchMedia;
}
