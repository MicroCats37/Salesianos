import { TriangleAlert } from "lucide-react";
import Link from "next/link";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface EstadoIndeterminadoProps {
  /** What is pending, in the words of the person who reads it. */
  titulo: string;
  /** Why it is pending and what is already done. */
  descripcion: string;
  /** The safe follow-up. It never repeats the operation that already ran. */
  accion?: { etiqueta: string; href?: string };
  className?: string;
}

/**
 * EstadoIndeterminado - the partial state (SH-03 S-09).
 *
 * The operation SUCCEEDED PARTIALLY: the money moved and the right did not
 * arrive yet. The state names the exact pending thing and offers a follow-up
 * that does not repeat the operation, because repeating it is what creates a
 * second charge.
 *
 * It is never painted as a success and it is never hidden.
 */
export function EstadoIndeterminado({
  titulo,
  descripcion,
  accion,
  className,
}: EstadoIndeterminadoProps) {
  return (
    <Alert className={cn("border-info/45 bg-info/10", className)}>
      <TriangleAlert className="size-4 text-info" aria-hidden="true" />
      <AlertTitle className="text-foreground">{titulo}</AlertTitle>
      <AlertDescription className="text-muted-foreground">
        {descripcion}
      </AlertDescription>
      {accion ? (
        <div className="mt-3">
          <Button asChild variant="outline" size="sm" className="min-h-11">
            {accion.href ? (
              <Link href={accion.href}>{accion.etiqueta}</Link>
            ) : (
              <span>{accion.etiqueta}</span>
            )}
          </Button>
        </div>
      ) : null}
    </Alert>
  );
}
