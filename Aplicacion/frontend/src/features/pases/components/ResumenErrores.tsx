"use client";

import { useEffect, useRef } from "react";
import type { FieldValues, UseFormReturn } from "react-hook-form";

export interface ResumenErroresProps<T extends FieldValues> {
  /** The form whose errors are summarized. */
  methods: UseFormReturn<T>;
}

/**
 * ResumenErrores - the summary of the errors of a form.
 *
 * It is the ONE summary of the feature: the two forms of passes share it, so
 * the wording and the focus behaviour are the same in both.
 *
 * It receives the focus after an invalid submit (`SH-02` A11Y-05) and it is
 * announced: it is an alert, not a paragraph. The error of every field is
 * ALSO drawn by `FormField` under its own control, so the message is never
 * only here.
 */
export function ResumenErrores<T extends FieldValues>({
  methods,
}: ResumenErroresProps<T>) {
  const referencia = useRef<HTMLDivElement>(null);
  const { errors, isSubmitted } = methods.formState;

  const mensajes = Object.values(errors)
    .map((error) => error?.message)
    .filter((mensaje): mensaje is string => Boolean(mensaje));

  useEffect(() => {
    if (!isSubmitted || mensajes.length === 0) return;
    referencia.current?.focus();
  }, [isSubmitted, mensajes.length]);

  if (!isSubmitted || mensajes.length === 0) return null;

  return (
    <div
      ref={referencia}
      role="alert"
      tabIndex={-1}
      className="rounded-[var(--radius-md)] border border-destructive/45 bg-destructive/10 px-3 py-2.5"
    >
      <p className="text-sm font-semibold text-foreground">
        Revisa {mensajes.length === 1 ? "este campo" : "estos campos"} antes de
        continuar.
      </p>
      <ul className="mt-1 flex flex-col gap-0.5">
        {mensajes.map((mensaje) => (
          <li key={mensaje} className="text-caption text-muted-foreground">
            {mensaje}
          </li>
        ))}
      </ul>
    </div>
  );
}
