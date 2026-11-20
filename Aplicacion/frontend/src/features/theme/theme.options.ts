import { Monitor, Moon, Sun } from "lucide-react";

/**
 * The three themes the product offers.
 *
 * `system` stays AVAILABLE but it is never the default: the visitor picks it
 * explicitly, and a visitor who never chose anything gets the light theme.
 */
export const THEME_OPTIONS = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Oscuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
] as const;

export type ThemeValue = (typeof THEME_OPTIONS)[number]["value"];

/**
 * The label of the active theme.
 *
 * An unknown value falls back to `light`, because that is the theme a
 * visitor without a stored preference gets.
 */
export function themeLabel(value: string | undefined | null): string {
  const opcion = THEME_OPTIONS.find((item) => item.value === value);

  return opcion?.label ?? "Claro";
}

/**
 * Whether a stored value is one of the three themes of the product.
 */
export function isThemeValue(value: unknown): value is ThemeValue {
  return THEME_OPTIONS.some((item) => item.value === value);
}
