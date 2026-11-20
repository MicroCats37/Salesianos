"use client";

import { Eye, EyeOff } from "lucide-react";

export interface ToggleContrasenaProps {
  /** Whether the password is being shown right now. */
  visible: boolean;
  /** The action that shows or hides the password. */
  onToggle: () => void;
  /**
   * The noun of the field.
   *
   * It names the FIELD, not the control: the accessible name says what the
   * button does with THAT password, so a screen reader never announces two
   * indistinguishable "Mostrar contraseña" in the same form.
   */
  campo: "contraseña" | "confirmación de la contraseña";
}

/**
 * ToggleContrasena - the button that shows and hides a password.
 *
 * It is ONE component for the whole feature: the registration and the access
 * share it, so the icon, the size, the accessible name and the motion are
 * the same in both (`features/auth`).
 *
 * The icon is decorative: the NAME of the button is what the screen reader
 * announces, and it changes with the state ("Mostrar" / "Ocultar").
 */
export function ToggleContrasena({
  visible,
  onToggle,
  campo,
}: ToggleContrasenaProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={visible ? `Ocultar ${campo}` : `Mostrar ${campo}`}
      className="absolute right-2 top-1/2 min-h-11 min-w-11 -translate-y-1/2 rounded-[var(--radius-sm)] p-2 text-muted-foreground transition-colors duration-(--motion-duration-fast) hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {visible ? (
        <EyeOff className="size-4" aria-hidden="true" />
      ) : (
        <Eye className="size-4" aria-hidden="true" />
      )}
    </button>
  );
}
