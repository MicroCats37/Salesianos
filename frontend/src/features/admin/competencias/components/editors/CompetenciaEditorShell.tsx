"use client";

import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import type { DefaultValues, FieldValues } from "react-hook-form";
import type { ZodType } from "zod";
import { GenericForm } from "@/components/genericForm/GenericForm";
import type { FormField } from "@/components/genericForm/GenericInput";
import { Button } from "@/components/ui/button";
import { CompetenciaErrorAlert } from "../CompetenciaErrorAlert";
import { CompetenciaCampo } from "./CompetenciaCampo";

export interface CompetenciaEditorShellProps<T extends FieldValues> {
  /** Title of the editor. */
  titulo: string;
  /** Explanation of what the editor does. */
  descripcion?: string;
  /** The Zod schema that validates the form. */
  esquema: ZodType<T, unknown>;
  /** The fields of the form (the single source of the layout). */
  campos: FormField[];
  /** The values the form starts with. */
  initialData?: DefaultValues<T>;
  /** The submission: it receives the validated data of the form. */
  onSubmit: (datos: T) => void | Promise<void>;
  /** The failure of the last command, if it failed. */
  error?: { message: string; status?: number } | null;
  /** Send the last data again. */
  onReintentar?: () => void;
  /** Whether a command is in flight. */
  isPending?: boolean;
  /** Label of the submit button. */
  submitLabel?: string;
  /** Label of the cancel button. */
  cancelLabel?: string;
  /** The action of the cancel button. */
  onCancel?: () => void;
  /** Extra content rendered under the fields. */
  children?: ReactNode;
}

/**
 * CompetenciaEditorShell — the shell shared by EVERY editor of the module.
 *
 * The shell owns the presentation only: the validation lives in Zod, the
 * state lives in React Hook Form and the payload lives in the mutation hook
 * (`contract/next-app-architecture-contract.md` §5).
 *
 * The failure of a command is rendered as an ALERT (with the role that the
 * assistive technologies announce) and it offers a retry: a conflict is
 * never a dead end.
 */
export function CompetenciaEditorShell<T extends FieldValues>({
  titulo,
  descripcion,
  esquema,
  campos,
  initialData,
  onSubmit,
  error,
  onReintentar,
  isPending = false,
  submitLabel = "Guardar",
  cancelLabel = "Cancelar",
  onCancel,
  children,
}: CompetenciaEditorShellProps<T>) {
  return (
    <section className="card-elevated space-y-4 p-4">
      <header className="space-y-1">
        <h3 className="text-sm font-black text-slate-900">{titulo}</h3>
        {descripcion ? (
          <p className="text-[11px] text-slate-500">{descripcion}</p>
        ) : null}
      </header>

      <GenericForm
        schema={esquema}
        fields={campos}
        initialData={initialData}
        onSubmit={onSubmit}
        isLoading={isPending}
        skipFooter
      >
        {({ isSubmitting }) => (
          <>
            <div className="grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-12">
              {campos.map((campo) => (
                <CompetenciaCampo key={campo.name} campo={campo} />
              ))}
            </div>

            {children}

            {error ? (
              <CompetenciaErrorAlert
                error={error}
                onReintentar={onReintentar}
              />
            ) : null}

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              {onCancel ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={onCancel}
                  disabled={isSubmitting}
                >
                  {cancelLabel}
                </Button>
              ) : null}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <Loader2
                    className="mr-2 h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                ) : null}
                {submitLabel}
              </Button>
            </div>
          </>
        )}
      </GenericForm>
    </section>
  );
}
