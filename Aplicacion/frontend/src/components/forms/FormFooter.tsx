import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface FormFooterProps {
  submitLabel: string;
  pendingLabel?: string;
  cancelLabel?: string;
  onCancel?: () => void;
  isSubmitting?: boolean;
  isDisabled?: boolean;
  className?: string;
}

export function FormFooter({
  submitLabel,
  pendingLabel = "Guardando…",
  cancelLabel = "Cancelar",
  onCancel,
  isSubmitting = false,
  isDisabled = false,
  className,
}: FormFooterProps) {
  const locked = isSubmitting || isDisabled;

  return (
    <div
      className={cn(
        "col-span-12 mt-2 flex flex-col-reverse items-stretch justify-between gap-3 sm:flex-row sm:items-center",
        className,
      )}
    >
      {onCancel ? (
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={locked}
          className="min-h-11 sm:min-w-[120px]"
        >
          {cancelLabel}
        </Button>
      ) : null}

      <Button
        type="submit"
        disabled={locked}
        className="min-h-11 sm:min-w-[160px]"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            {pendingLabel}
          </>
        ) : (
          submitLabel
        )}
      </Button>
    </div>
  );
}
