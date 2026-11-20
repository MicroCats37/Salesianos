// genericForm/visibility.tsx
//
// Visibility of the fields and of the sections of a form.
//
// A field may depend on other fields: `hidden` is a predicate over the
// values of the form. Reading those values with a global `watch()` inside the
// GenericForm re-renders the WHOLE form on every keystroke, which the
// frontend contract forbids explicitly (`contract/smart.md` §5.2).
//
// The rule of this module:
//
// - A field that declares `dependsOn` reads ONLY those fields, through
//   `useWatch`, so a change of an unrelated field never re-renders it.
// - A field that does NOT declare its dependencies keeps the legacy
//   behaviour: it reads the whole form. That is the compatibility path for
//   the configurations that exist today.
// - A field whose visibility is a plain boolean reads nothing at all.
//
// The three cases are three DIFFERENT components on purpose: the number of
// hooks of a component must never depend on a runtime condition.

"use client";

import type { ReactNode } from "react";
import type { Control, FieldValues } from "react-hook-form";
import { useWatch } from "react-hook-form";
import type { FormField, FormSection } from "./GenericInput";

// ── Strategies ───────────────────────────────────────────────────────────────

type VisibilityStrategy =
  | { kind: "static"; hidden: boolean }
  | { kind: "named"; names: readonly string[] }
  | { kind: "all" };

function fieldStrategy(field: FormField): VisibilityStrategy {
  if (typeof field.hidden !== "function") {
    return { kind: "static", hidden: Boolean(field.hidden) };
  }

  const dependencies = field.dependsOn;
  if (Array.isArray(dependencies) && dependencies.length > 0) {
    return { kind: "named", names: dependencies };
  }

  return { kind: "all" };
}

function sectionStrategy(section: FormSection): VisibilityStrategy {
  const names: string[] = [];
  let needsWholeForm = false;

  for (const field of section.fields) {
    const strategy = fieldStrategy(field);
    if (strategy.kind === "all") {
      needsWholeForm = true;
      break;
    }
    if (strategy.kind === "named") {
      for (const name of strategy.names) {
        if (!names.includes(name)) names.push(name);
      }
    }
  }

  if (needsWholeForm) return { kind: "all" };
  if (names.length > 0) return { kind: "named", names };

  // Every field has a static visibility: the section is empty when all of
  // them are hidden.
  return {
    kind: "static",
    hidden: section.fields.every(
      (field) => typeof field.hidden !== "function" && Boolean(field.hidden),
    ),
  };
}

// ── Gates ────────────────────────────────────────────────────────────────────

interface GateProps {
  strategy: VisibilityStrategy;
  control: Control<FieldValues>;
  compute: (values: Record<string, unknown>) => boolean;
  children: ReactNode;
}

const StaticGate = ({
  hidden,
  children,
}: {
  hidden: boolean;
  children: ReactNode;
}) => (hidden ? null : <>{children}</>);

const NamedGate = ({
  names,
  control,
  compute,
  children,
}: {
  names: readonly string[];
  control: Control<FieldValues>;
  compute: (values: Record<string, unknown>) => boolean;
  children: ReactNode;
}) => {
  const watched = useWatch({
    control,
    name: names as string[],
  }) as unknown[];

  const values: Record<string, unknown> = {};
  names.forEach((name, index) => {
    values[name] = watched[index];
  });

  return compute(values) ? null : <>{children}</>;
};

const WholeFormGate = ({
  control,
  compute,
  children,
}: {
  control: Control<FieldValues>;
  compute: (values: Record<string, unknown>) => boolean;
  children: ReactNode;
}) => {
  const values = useWatch({ control }) as Record<string, unknown>;
  return compute(values) ? null : <>{children}</>;
};

const Gate = ({ strategy, control, compute, children }: GateProps) => {
  if (strategy.kind === "static") {
    return <StaticGate hidden={strategy.hidden}>{children}</StaticGate>;
  }
  if (strategy.kind === "named") {
    return (
      <NamedGate
        names={strategy.names}
        control={control}
        compute={compute}
        children={children}
      />
    );
  }
  return (
    <WholeFormGate control={control} compute={compute} children={children} />
  );
};

// ── Public gates ─────────────────────────────────────────────────────────────

function isFieldHidden(
  field: FormField,
  values: Record<string, unknown>,
): boolean {
  if (typeof field.hidden === "function") {
    return Boolean(field.hidden(values));
  }
  return Boolean(field.hidden);
}

interface FieldVisibilityProps {
  field: FormField;
  control: Control<FieldValues>;
  children: ReactNode;
}

/**
 * Renders the children of a field only when the field is visible.
 */
export const FieldVisibility = ({
  field,
  control,
  children,
}: FieldVisibilityProps) => (
  <Gate
    strategy={fieldStrategy(field)}
    control={control}
    compute={(values) => isFieldHidden(field, values)}
  >
    {children}
  </Gate>
);

interface SectionVisibilityProps {
  section: FormSection;
  control: Control<FieldValues>;
  children: ReactNode;
}

/**
 * Renders the children of a section only when the section holds at least one
 * visible field.
 */
export const SectionVisibility = ({
  section,
  control,
  children,
}: SectionVisibilityProps) => (
  <Gate
    strategy={sectionStrategy(section)}
    control={control}
    compute={(values) =>
      section.fields.every((field) => isFieldHidden(field, values))
    }
  >
    {children}
  </Gate>
);
