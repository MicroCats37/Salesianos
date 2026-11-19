import { Construction } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * RoutePlaceholder - the shell of a route whose view is not built yet.
 *
 * FND-06 owns the ROUTING and the CHROME, not the domain views. This
 * placeholder makes that explicit instead of leaving a blank page: it shows
 * the identity of the route, the task it will own, and which packet will
 * build it.
 *
 * It is removed by the UI-0x packet that owns the route.
 */
export interface RoutePlaceholderProps {
  /** Plan page ID, e.g. `ADM-05`. */
  pageId: string;
  /** The task the route will own, in one line. */
  tarea: string;
  /** The packet that builds the view. */
  packet: string;
  children?: ReactNode;
  className?: string;
}

export function RoutePlaceholder({
  pageId,
  tarea,
  packet,
  children,
  className,
}: RoutePlaceholderProps) {
  return (
    <div className={cn("flex flex-col gap-6", className)}>
      <header className="flex flex-col gap-2">
        <p className="text-eyebrow-brand text-primary">{pageId}</p>
        <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
          {tarea}
        </h1>
      </header>

      {children}

      <div className="flex items-start gap-3 rounded-[--radius-lg] border border-dashed border-border bg-surface-recessed p-6">
        <Construction
          className="mt-0.5 size-5 shrink-0 text-muted-foreground"
          aria-hidden="true"
        />
        <div className="flex flex-col gap-1">
          <p className="font-semibold text-foreground">
            Ruta conectada, vista pendiente
          </p>
          <p className="text-sm text-muted-foreground">
            Esta ruta ya existe en la navegación y en el contrato de rutas. La
            construyen los paquetes <code className="font-mono">{packet}</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
