import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function resolveImageUrl(path: string | null | undefined): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "";
  return `${baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

/**
 * Strips all non-digit characters from a string.
 * Used for phone/document number inputs.
 */
export function stripNonDigits(value: string): string {
  return value.replace(/\D/g, "");
}
