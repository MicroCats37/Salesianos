"use client";

import { useTheme } from "next-themes";
import {
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import {
  isThemeValue,
  THEME_OPTIONS,
  type ThemeValue,
} from "@/features/theme/theme.options";

export interface ThemeMenuItemsProps {
  /** Extra classes of the group, for the surfaces that need another tone. */
  className?: string;
}

/**
 * ThemeMenuItems - the three themes as a radio group.
 *
 * It is a RADIO group and not three buttons: the visitor has to see which
 * one is active, and a radio is the control that says that. The group lives
 * in its own module so the selector of la barra y el del menú del usuario
 * offer exactly the same options.
 */
export function ThemeMenuItems({ className }: ThemeMenuItemsProps) {
  const { theme, setTheme } = useTheme();

  const valor = isThemeValue(theme) ? theme : "light";

  return (
    <DropdownMenuRadioGroup
      value={valor}
      onValueChange={(siguiente) => setTheme(siguiente as ThemeValue)}
      className={className}
    >
      {THEME_OPTIONS.map((opcion) => (
        <DropdownMenuRadioItem
          key={opcion.value}
          value={opcion.value}
          className="min-h-9 gap-2"
        >
          <opcion.icon
            className="size-4 text-muted-foreground"
            aria-hidden="true"
          />
          {opcion.label}
        </DropdownMenuRadioItem>
      ))}
    </DropdownMenuRadioGroup>
  );
}
