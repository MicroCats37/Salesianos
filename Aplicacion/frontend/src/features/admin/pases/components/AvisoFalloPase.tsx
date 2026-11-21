import { Lock, type LucideIcon, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EstadoDeFallo } from "../utils/admin.pase.utils";

export interface AvisoFalloPaseProps {
  /** The failure, already translated into the language of the interface. */
  fallo: EstadoDeFallo;
  className?: string;
}

/**
 * The ICON of each kind of failure.
 *
 * The kind comes from the HTTP STATUS of the answer, never from the machine
 * code: the catalogue of public codes is not closed.
 */
const ICONOS: Record<EstadoDeFallo["tipo"], LucideIcon> = {
  conflicto: TriangleAlert,
  validacion: TriangleAlert,
  permiso: Lock,
  sesion: Lock,
  desconocido: TriangleAlert,
};

/**
 * AvisoFalloPase - the notice of a failure of the backend.
 *
 * The prose of the backend is printed VERBATIM: the public message of the
 * frozen catalogue is the truth of the failure and the interface never
 * re-writes it.
 *
 * The notice is an `alert`: a reader of screen hears it without moving the
 * focus, which is what an operation that did NOT happen requires.
 */
export function AvisoFalloPase({ fallo, className }: AvisoFalloPaseProps) {
  const Icono = ICONOS[fallo.tipo] ?? TriangleAlert;

  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive",
        className,
      )}
    >
      <Icono className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div className="flex flex-col gap-1">
        <p className="font-semibold">{fallo.titulo}</p>
        <p>{fallo.mensaje}</p>
        {fallo.tipo === "conflicto" ? (
          <p className="text-caption">
            El estado actual del recurso no permite la operación: si la persona
            ya tiene una entrada activa de este pase en esta edición, el
            servidor no crea un segundo derecho.
          </p>
        ) : null}
      </div>
    </div>
  );
}
