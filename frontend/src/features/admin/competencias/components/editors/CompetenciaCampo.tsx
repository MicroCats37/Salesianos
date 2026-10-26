"use client";

import { useFormContext } from "react-hook-form";
import type { FormField } from "@/components/genericForm/GenericInput";
import { GenericInput } from "@/components/genericForm/GenericInput";

export interface CompetenciaCampoProps {
  /** The configuration of the field: the shared registry resolves the input. */
  campo: FormField;
}

/**
 * CompetenciaCampo — ONE field of an editor of the module.
 *
 * The field is rendered with the shared `GenericInput`, so the label, the
 * helper text and the error message are the shared ones of the application.
 *
 * The state comes from the context of `GenericForm`: the component NEVER owns
 * a value and NEVER validates by itself
 * (`contract/smart.md` §2 — the truth lives in Zod).
 */
export function CompetenciaCampo({ campo }: CompetenciaCampoProps) {
  const { register, control, formState } = useFormContext();

  return (
    <GenericInput
      field={campo}
      register={register}
      control={control}
      errors={formState.errors}
    />
  );
}
