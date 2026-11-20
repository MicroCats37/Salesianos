"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import type { ComponentType, FC, ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  type DefaultValues,
  type FieldValues,
  FormProvider as Form,
  type Path,
  type UseFormReturn,
  useForm,
} from "react-hook-form";
import type { ZodType } from "zod";
import { Button } from "@/components/ui/button";
import {
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { handleApiError, notify } from "@/errors";
import { buildCreatePayload } from "@/lib/forms/buildCreatePayload";
import { buildUpdatePayload } from "@/lib/forms/buildUpdatePayload";
import { stableSerialize } from "@/lib/forms/stableSerialize";
import { isSameFormValue } from "@/lib/forms/valueEquality";
import { buildFormDefaults } from "./formDefaults";
import {
  type FieldWrapperProps,
  type FormField,
  type FormSection,
  GenericInput,
  type SectionWrapperProps,
} from "./GenericInput";
import { FieldVisibility, SectionVisibility } from "./visibility";

// =====================================================================
// DEBUG FLAG — silent Zod/RHF validation error logging
// =====================================================================
// Enable via NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS=true in .env.local
// Safe by default (false) — only logs when explicitly enabled.

const DEBUG_FORM = process.env.NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS === "true";

// =====================================================================
// INTERNAL DEFAULT WRAPPERS
// =====================================================================

// 1. Ghost (Invisible): For simple/flat forms
const GhostWrapper: FC<SectionWrapperProps> = ({
  children,
  title,
  className,
}) => (
  <div className={`w-full ${className || ""}`}>
    {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
    {children}
  </div>
);

// 2. Card (Standard): Design with border and shadow
const CardWrapper: FC<SectionWrapperProps> = ({
  children,
  title,
  description,
  icon: Icon,
  className,
}) => (
  <div
    className={`border rounded-xl p-3 md:p-4 bg-card shadow-sm ${className || ""}`}
  >
    <div className="flex flex-col gap-0.5 mb-3 pb-2 border-b">
      <div className="flex items-center gap-2">
        {Icon && (
          <div className="p-1 bg-primary/10 rounded-md text-primary">
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
        <h3 className="font-semibold text-sm md:text-base tracking-tight">
          {title}
        </h3>
      </div>
      {description && (
        <p className="text-[10px] md:text-xs text-muted-foreground ml-0.5">
          {description}
        </p>
      )}
    </div>
    {children}
  </div>
);

// =====================================================================
// VALUE MAPPING
// =====================================================================

/**
 * Maps the value of a SELECT or a RADIO to the value declared by its option.
 *
 * The DOM only carries strings: the mapping is the IDENTITY of the option
 * (`"3"` IS the option `3`), NOT a type coercion. The coercion belongs to
 * Zod, which has already produced the values of the form.
 *
 * `undefined` and `null` are values and travel untouched: `undefined` means
 * "never filled" and `null` means "explicitly empty".
 */
function mapOptionValues(
  data: FieldValues,
  fields: readonly FormField[],
): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null) {
      result[key] = value;
      continue;
    }

    const field = fields.find((candidate) => candidate.name === key);
    if (!field || (field.type !== "radio" && field.type !== "select")) {
      result[key] = value;
      continue;
    }

    const option = field.options?.find(
      (candidate) => String(candidate.value) === String(value),
    );

    result[key] = option ? option.value : value;
  }

  return result;
}

// =====================================================================
// MAIN COMPONENT
// =====================================================================

type CustomFieldRenderer<T extends FieldValues> = (
  methods: UseFormReturn<T>,
) => ReactNode;

export interface GenericFormProps<T extends FieldValues> {
  // A. DATA (Automatic Mode)
  formSections?: FormSection[]; // Complex structure
  fields?: FormField[]; // Simple structure (flat)

  // B. LOGICAL CONTROL
  schema: ZodType<T, any, any>;
  onSubmit: (data: T) => any | Promise<any>;
  initialData?: DefaultValues<T>;

  // C. UI CUSTOMIZATION (Hybrid Mode)
  title?: string;
  description?: string;
  submitButtonText?: string;
  cancelButtonText?: string;
  onCancel?: () => void;
  isLoading?: boolean;
  isDisabled?: boolean;
  activateSubmitButton?: boolean;
  formMethods?: UseFormReturn<T>;

  // UI Injections (Wrappers and Custom Footer)
  globalSectionWrapper?: ComponentType<SectionWrapperProps>; // Change all Cards
  globalFieldWrapper?: ComponentType<FieldWrapperProps>; // Change all Inputs
  renderFooter?: (props: {
    // Change buttons
    isSubmitting: boolean;
    onCancel?: () => void;
    onSubmit: () => void;
    methods: UseFormReturn<T>;
  }) => ReactNode;

  formClassName?: string; // Classes for the <form> tag
  formId?: string; // HTML id for the <form> element (enables form="..." on external submit buttons)

  // D. TOTAL CONTROL (Manual Mode)
  // If you use this, you draw ALL the HTML inside (inputs, layouts, and buttons).
  children?: (props: {
    methods: UseFormReturn<T>;
    isSubmitting: boolean;
    onSubmit: () => void;
    submissionMessage: { type: "success" | "error"; message: string } | null;
  }) => ReactNode;

  // E. EXTRAS
  onFieldChange?: (fieldName: string, value: any) => void;
  customFields?: Record<string, CustomFieldRenderer<T>>;
  showErrorsAsToasts?: boolean;

  /**
   * The wire mapping the submit uses.
   *
   * - `"create"` (the default): the FULL validated create mapping. Every
   *   declared field that carries a value travels. A create has no previous
   *   state, so nothing is diffed.
   * - `"update"`: the STRICT update mapping. A value that is EQUAL to the one
   *   of `initialData` is omitted, because the user did not touch it.
   *
   * The two mappings are never mixed: a create NEVER uses update-diff
   * semantics.
   */
  submitMode?: "create" | "update";

  /**
   * Re-hydrates the form when the data it edits changes (the default).
   *
   * The re-hydration is DETERMINISTIC: it happens when the CONTENT of
   * `initialData` changes, not when its reference does, so a parent that
   * rebuilds the object on every render never resets the form twice.
   *
   * Pass `false` to keep the values the user typed when the record changes.
   */
  resetOnInitialDataChange?: boolean;

  // F. FOOTER CONTROL
  /**
   * Suppresses the internal default footer when true.
   * Use with GenericModal.Footer for external submit/cancel buttons
   * linked via form="..." on the submit button.
   */
  skipFooter?: boolean;
}

export const GenericForm = <T extends FieldValues>({
  formSections,
  fields,
  schema,
  onSubmit,
  title,
  description,
  initialData,
  submitButtonText = "Submit",
  cancelButtonText = "Cancel",
  onCancel,
  onFieldChange,
  customFields = {},
  isLoading = false,
  isDisabled = false,
  activateSubmitButton = true,
  formMethods,

  // Custom injections
  globalSectionWrapper,
  globalFieldWrapper,
  renderFooter,
  formClassName,
  formId,
  children, // Render prop for manual mode
  showErrorsAsToasts = false,
  skipFooter = false,
  submitMode = "create",
  resetOnInitialDataChange = true,
}: GenericFormProps<T>) => {
  // 1. NORMALIZATION (Only matters if NOT using 'children')
  let normalizedSections: FormSection[] = [];
  let allFieldsFlat: FormField[] = [];

  if (formSections && formSections.length > 0) {
    normalizedSections = formSections;
    allFieldsFlat = formSections.flatMap((s) => s.fields);
  } else if (fields && fields.length > 0) {
    normalizedSections = [{ title: "", fields: fields, wrapper: GhostWrapper }];
    allFieldsFlat = fields;
  }

  // 2. REACT HOOK FORM SETUP
  const defaults = buildFormDefaults(initialData, allFieldsFlat);

  const internalMethods = useForm<T>({
    resolver: zodResolver(schema),
    defaultValues: defaults,
  });

  const methods =
    (formMethods as UseFormReturn<T>) || (internalMethods as UseFormReturn<T>);

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors, isSubmitting },
  } = methods;

  const [submissionMessage, setSubmissionMessage] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // The fields that carry a SERVER error, so a new attempt starts clean.
  const serverErrorFieldsRef = useRef<string[]>([]);

  // The fields of the form live in a ref: the re-hydration effect must not
  // depend on the identity of the array.
  const fieldsRef = useRef<FormField[]>(allFieldsFlat);
  fieldsRef.current = allFieldsFlat;

  // 3. RE-HYDRATION
  //
  // The form is re-hydrated when the CONTENT of `initialData` changes: the
  // record that is being edited changed, or the data of the edit form
  // arrived asynchronously.
  const initialDataKey = useMemo(
    () => stableSerialize(initialData),
    [initialData],
  );
  const hydratedKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (!resetOnInitialDataChange) return;
    // The data did not change: there is nothing to re-hydrate.
    if (hydratedKeyRef.current === initialDataKey) return;
    // A submission in flight is never interrupted by a re-hydration.
    if (isSubmitting) return;

    const isFirstHydration = hydratedKeyRef.current === null;
    hydratedKeyRef.current = initialDataKey;

    // The first values were already given to `useForm` as default values.
    if (isFirstHydration) return;

    // The data the form already holds IS the new data: a parent that feeds
    // the live values back as `initialData` must never reset the form.
    if (isSameFormValue(methods.getValues(), initialData)) return;

    methods.reset(buildFormDefaults(initialData, fieldsRef.current));
  }, [
    initialDataKey,
    initialData,
    isSubmitting,
    methods,
    resetOnInitialDataChange,
  ]);

  useEffect(() => {
    if (onFieldChange) {
      const subscription = watch((value, { name }) => {
        if (name) onFieldChange(name, value[name as string]);
      });
      return () => subscription.unsubscribe();
    }
  }, [watch, onFieldChange]);

  // 4. SUBMIT HANDLER
  const handleFormSubmit = async (data: FieldValues) => {
    setSubmissionMessage(null);

    // A new attempt starts without the errors of the previous one.
    for (const field of serverErrorFieldsRef.current) {
      methods.clearErrors(field as Path<T>);
    }
    serverErrorFieldsRef.current = [];

    // The values are the OUTPUT of the Zod validation: Zod owns the
    // validation AND the coercion. The form NEVER re-coerces a value, and it
    // NEVER destroys an `undefined`, a `null` or a `File`.
    const processedData = mapOptionValues(data, allFieldsFlat);

    const finalData =
      submitMode === "update"
        ? buildUpdatePayload(
            processedData as Record<string, unknown>,
            initialData as unknown as
              | Partial<Record<string, unknown>>
              | undefined,
            schema as unknown as ZodType<Record<string, unknown>>,
            { strict: true },
          )
        : buildCreatePayload(
            processedData as Record<string, unknown>,
            schema as unknown as ZodType<Record<string, unknown>>,
          );

    try {
      await onSubmit(finalData as unknown as T);
      setSubmissionMessage({
        type: "success",
        message: "Operation successful!",
      });
    } catch (e: any) {
      const errorRes = handleApiError(e);
      setSubmissionMessage({ type: "error", message: errorRes.message });

      // The field errors of the response reach the control they belong to.
      // The map has ONE entry per field, so `setError` is called EXACTLY ONCE
      // per field.
      if (errorRes.fieldErrors) {
        const fieldEntries = Object.entries(errorRes.fieldErrors);

        for (const [field, message] of fieldEntries) {
          methods.setError(field as any, {
            type: "server",
            message: message as string,
          });
        }

        serverErrorFieldsRef.current = fieldEntries.map(([field]) => field);
      }
    }
  };

  const isLocked = isSubmitting || isLoading || isDisabled;
  const onSubmitFn = handleSubmit(handleFormSubmit, (errs) => {
    if (DEBUG_FORM) {
      console.warn("[GenericForm] Zod validation error:", errs);
      // Recursive function to extract all error messages from a nested object
      const collectErrors = (obj: unknown, path = ""): string[] => {
        if (!obj) return [];
        if (typeof obj !== "object") return [];
        if ("message" in obj && typeof (obj as any).message === "string") {
          return [`${path}: ${(obj as any).message}`];
        }
        return Object.entries(obj as Record<string, unknown>).flatMap(
          ([key, val]) => collectErrors(val, path ? `${path}.${key}` : key),
        );
      };
      const allErrors = collectErrors(errs);
      console.warn("[GenericForm] Validation errors detail:", allErrors);
    }

    if (showErrorsAsToasts) {
      const showAllErrors = (obj: unknown) => {
        if (!obj) return;
        if (typeof obj !== "object") return;
        if ("message" in obj && typeof (obj as any).message === "string") {
          notify.error((obj as any).message);
          return;
        }
        Object.values(obj as Record<string, unknown>).forEach((val) =>
          showAllErrors(val),
        );
      };
      showAllErrors(errs);
    }
  });

  // A. MANUAL MODE (TOTAL USER CONTROL)
  if (children) {
    return (
      <Form {...methods}>
        <form id={formId} onSubmit={onSubmitFn} className={formClassName}>
          {children({
            methods,
            isSubmitting: isLocked,
            onSubmit: onSubmitFn,
            submissionMessage,
          })}
        </form>
      </Form>
    );
  }

  // B. AUTOMATIC / HYBRID MODE (SECTIONS AND CARDS)
  const DefaultFooter = (
    <div className="flex justify-end gap-3 mt-4">
      {onCancel && (
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLocked}
        >
          {cancelButtonText}
        </Button>
      )}
      {activateSubmitButton && (
        <Button type="submit" disabled={isLocked}>
          {isLocked && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {submitButtonText}
        </Button>
      )}
    </div>
  );

  return (
    <div className="w-full mx-auto border-0 shadow-none py-0 bg-none opacity-100">
      {(title || description) && (
        <CardHeader className="px-0 pb-6">
          {title && <CardTitle className="text-2xl">{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent className="px-0 gap-2">
        <Form {...methods}>
          <form
            id={formId}
            onSubmit={onSubmitFn}
            className={`space-y-4 ${formClassName || ""}`}
          >
            <fieldset disabled={isLocked} className="space-y-4">
              {normalizedSections.map((section, idx) => {
                // Wrapper Priority: Global -> Section -> Default (Card/Ghost)
                const Container =
                  globalSectionWrapper ||
                  section.wrapper ||
                  (formSections ? CardWrapper : GhostWrapper);

                // The visibility of the section AND of every field is
                // resolved by the visibility gates: a field that declares its
                // dependencies reads only those fields, so the form never
                // re-renders on every keystroke.
                return (
                  <SectionVisibility
                    key={`section-${idx}`}
                    section={section}
                    control={control as any}
                  >
                    <Container
                      title={section.title}
                      description={section.description}
                      icon={section.icon}
                      className={section.className}
                    >
                      <div className=" grid grid-cols-1 md:grid-cols-12 gap-x-4">
                        {section.fields.map((field) => (
                          <FieldVisibility
                            key={field.name}
                            field={field}
                            control={control as any}
                          >
                            {customFields[field.name] ? (
                              <div
                                className={`w-full ${field.containerClassName || "col-span-12"}`}
                              >
                                {customFields[field.name](methods)}
                              </div>
                            ) : (
                              <GenericInput
                                field={field}
                                register={register as any}
                                control={control as any}
                                errors={errors}
                                FieldWrapper={globalFieldWrapper}
                              />
                            )}
                          </FieldVisibility>
                        ))}
                      </div>
                    </Container>
                  </SectionVisibility>
                );
              })}
            </fieldset>

            {/* Dynamic Footer: Either custom, suppressed, or default */}
            {skipFooter
              ? null
              : renderFooter
                ? renderFooter({
                    isSubmitting: isLocked,
                    onCancel,
                    onSubmit: onSubmitFn,
                    methods,
                  })
                : DefaultFooter}
          </form>
        </Form>
      </CardContent>
    </div>
  );
};
