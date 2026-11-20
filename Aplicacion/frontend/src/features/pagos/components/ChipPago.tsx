import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * The action that the chip offers.
 *
 * A chip WITHOUT an action shows a state and no dead end: a button that
 * cannot do anything is a dead end (`SH-03` §2).
 */
export interface AccionChipPago {
  /** The wording of the action. */
  etiqueta?: string;
  /** The destination, when the action navigates. */
  href?: string;
  /** What the action does, when it stays on the screen. */
  onClick?: () => void;
}

export interface ChipPagoProps {
  /**
   * The wording of the backend.
   *
   * It is printed VERBATIM: the interface never rewrites the wording the
   * server chose (`SH-03` §6).
   */
  etiqueta: string;
  /**
   * The explanation of the backend.
   *
   * It is shown only when the surface asks for it: an explanation that is
   * always on screen is noise, not information.
   */
  descripcion?: string;
  /** The shape of the icon that accompanies the colour. */
  icono: LucideIcon;
  /** The classes of the surface of the chip. */
  superficie: string;
  /** The classes of the stroke of the icon. */
  trazo: string;
  /** The next step, when this surface offers one. */
  accion?: AccionChipPago;
  className?: string;
}

/**
 * ChipPago - the shared surface of a payment verdict.
 *
 * It is DUMB on purpose: it receives the wording, the explanation, the icon
 * and the painted classes, and it draws them. It knows NOTHING about the
 * business, so it imports no type of any other feature and it never decides
 * what a verdict means.
 *
 * Why it lives in the payment area: the visual payment component is SHARED
 * by the checkouts of inscripción, pases and tienda (`GOV-02-RB-02a`). The
 * payment area owns it and every surface composes it.
 *
 * Three things always travel together: the SHAPE of the icon, the COLOUR of
 * the bucket and the LABEL of the backend. The colour never carries the
 * meaning alone (`SH-01` §3.2, `ui-ux-pro-max` priority 1).
 */
export function ChipPago({
  etiqueta,
  descripcion,
  icono: Icono,
  superficie,
  trazo,
  accion,
  className,
}: ChipPagoProps) {
  return (
    <span className={cn("inline-flex flex-col gap-1.5", className)}>
      <span
        className={cn(
          "inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1",
          superficie,
        )}
      >
        <Icono className={cn("size-3.5 shrink-0", trazo)} aria-hidden="true" />
        <span className="text-xs font-semibold text-foreground">
          {etiqueta}
        </span>
      </span>

      {descripcion ? (
        <span className="text-caption text-muted-foreground">
          {descripcion}
        </span>
      ) : null}

      {accion ? (
        accion.href ? (
          <Button
            asChild
            variant="outline"
            size="sm"
            className="min-h-11 w-fit"
          >
            <Link href={accion.href}>{accion.etiqueta}</Link>
          </Button>
        ) : (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="min-h-11 w-fit"
            onClick={accion.onClick}
          >
            {accion.etiqueta}
          </Button>
        )
      ) : null}
    </span>
  );
}
