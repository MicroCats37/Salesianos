import Link from "next/link";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";

/**
 * The 404 of the administration area.
 *
 * The surface never confirms the existence of a resource that is out of its
 * scope: a record that belongs to another edition is the same 404 that a
 * record that does not exist is.
 */
export default function NotFound() {
  return (
    <div className="mx-auto flex w-full max-w-page flex-col gap-6 py-8">
      <div className="flex flex-col gap-3 border-b border-border pb-6">
        <p className="text-eyebrow-brand text-primary">Error 404</p>
        <h1 className="text-title-page text-foreground">
          No encontramos este registro
        </h1>
        <p className="max-w-measure text-lead text-muted-foreground">
          Puede que el registro no exista, que pertenezca a otra edición o que
          el enlace no sea correcto.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button asChild className="min-h-11">
          <Link href={RUTAS.administracion.resumen}>Volver al resumen</Link>
        </Button>
        <Button variant="outline" asChild className="min-h-11">
          <Link href={RUTAS.publico.inicio}>Ir al inicio</Link>
        </Button>
      </div>
    </div>
  );
}
