import type { LucideIcon } from "lucide-react";
import { TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { FieldIcon } from "./field-control";

export type FormFieldSpan = 3 | 4 | 6 | 8 | 12;

const SPAN: Record<FormFieldSpan, string> = {
  3: "col-span-12 md:col-span-3",
  4: "col-span-12 md:col-span-4",
  6: "col-span-12 md:col-span-6",
  8: "col-span-12 md:col-span-8",
  12: "col-span-12",
};

export interface FormFieldControl {
  id: string;
  "aria-invalid": true | undefined;
  "aria-describedby": string | undefined;
}

export interface FormFieldProps {
  id: string;
  label: string;
  required?: boolean;
  error?: string;
  helper?: string;
  description?: string;
  icon?: LucideIcon;
  span?: FormFieldSpan;
  className?: string;
  children: (control: FormFieldControl) => ReactNode;
}

export function FormField({
  id,
  label,
  required = false,
  error,
  helper,
  description,
  icon,
  span = 12,
  className,
  children,
}: FormFieldProps) {
  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;

  const control: FormFieldControl = {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? errorId : helper ? helperId : undefined,
  };

  return (
    <div className={cn("flex flex-col gap-1.5", SPAN[span], className)}>
      <label
        htmlFor={id}
        className="label-brand inline-flex items-center gap-1.5"
      >
        {label}
        {required ? (
          <span aria-hidden="true" className="text-destructive">
            *
          </span>
        ) : null}
      </label>

      <div
        className={cn(
          "relative [&_button:not([data-slot=checkbox])]:min-h-11 [&_input]:min-h-11 [&_textarea]:min-h-11",
          icon &&
            "[&_button:not([data-slot=checkbox])]:pl-10 [&_input]:pl-10 [&_textarea]:pl-10",
        )}
      >
        {icon ? <FieldIcon icon={icon} invalid={Boolean(error)} /> : null}
        {children(control)}
      </div>

      {error ? (
        <p
          id={errorId}
          role="alert"
          className="text-caption flex items-center gap-1.5 text-destructive"
        >
          <TriangleAlert className="size-3.5 shrink-0" aria-hidden="true" />
          {error}
        </p>
      ) : helper ? (
        <p id={helperId} className="text-caption text-muted-foreground">
          {helper}
        </p>
      ) : description ? (
        <p className="text-caption text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}
