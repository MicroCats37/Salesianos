"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ThemeMenuItems } from "@/features/theme/ThemeMenuItems";
import {
  isThemeValue,
  THEME_OPTIONS,
  themeLabel,
} from "@/features/theme/theme.options";
import { cn } from "@/lib/utils";

export interface ThemeToggleProps {
  /** Extra classes of the trigger button. */
  className?: string;
  /** Alignment of the menu against the trigger. */
  align?: "start" | "center" | "end";
}

/**
 * ThemeToggle - the selector of the visual theme.
 *
 * It is NOT a button that swaps an icon: the trigger always NAMES the state
 * it is in ("Tema: Oscuro"), in its accessible name and in its tooltip, and
 * the menu marks the active option with a radio. A visitor who cannot see
 * the colour still knows which theme is active.
 *
 * The hydration is resolved before anything is shown: `next-themes` cannot
 * know the stored preference during the server render, so the trigger is
 * only painted once the client has read it. Before that, the space is
 * reserved and nothing is announced.
 */
export function ThemeToggle({ className, align = "end" }: ThemeToggleProps) {
  const { theme } = useTheme();
  const [montado, setMontado] = useState(false);

  useEffect(() => {
    setMontado(true);
  }, []);

  const valor = isThemeValue(theme) ? theme : "light";
  const opcion =
    THEME_OPTIONS.find((item) => item.value === valor) ?? THEME_OPTIONS[0];
  const Icono = opcion.icon;
  const nombreEstado = `Tema: ${themeLabel(montado ? theme : "light")}`;

  return (
    <div className="inline-flex size-11 items-center justify-center">
      {!montado ? (
        <span
          aria-hidden="true"
          className="block size-11 rounded-[var(--radius-md)]"
        />
      ) : (
        <DropdownMenu>
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("size-11", className)}
                  aria-label={nombreEstado}
                >
                  <Icono className="size-5" aria-hidden="true" />
                </Button>
              </DropdownMenuTrigger>
            </TooltipTrigger>
            <TooltipContent side="bottom">{nombreEstado}</TooltipContent>
          </Tooltip>
          <DropdownMenuContent align={align} className="w-44">
            <DropdownMenuLabel>Tema</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <ThemeMenuItems />
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}
