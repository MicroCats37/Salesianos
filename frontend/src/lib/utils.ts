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

/** Strip all non-digit characters from a string (for phone/DNI fields). */
export function stripNonDigits(value: string): string {
  return value.replace(/\D/g, "");
}

/** Strip all non-alphanumeric characters from a string (for PAS fields). */
export function stripNonAlphanumeric(value: string): string {
  return value.replace(/[^a-zA-Z0-9]/g, "");
}
