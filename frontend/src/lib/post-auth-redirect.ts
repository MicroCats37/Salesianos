"use client";

import { POST_AUTH_REDIRECT_KEY } from "@/components/event/PreinscribirCta";

/**
 * Consume the post-auth redirect destination previously stashed in
 * sessionStorage by `PreinscribirCta` (or any other CTA that wants to send
 * the user back where they were going after they authenticate).
 *
 * Returns the destination path if one was stashed, otherwise null. Always
 * removes the key after reading so subsequent navigations don't replay it.
 *
 * Safe to call during SSR (returns null).
 */
export function consumePostAuthRedirect(): string | null {
  if (typeof window === "undefined") return null;
  const dest = window.sessionStorage.getItem(POST_AUTH_REDIRECT_KEY);
  if (dest) {
    window.sessionStorage.removeItem(POST_AUTH_REDIRECT_KEY);
  }
  return dest;
}
