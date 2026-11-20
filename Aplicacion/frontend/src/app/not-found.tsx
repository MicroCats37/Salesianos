import { BrandMark } from "@/components/brand/BrandMark";
import { Button } from "@/components/ui/button";
import { RUTAS } from "@/lib/routes";

/**
 * The global 404.
 *
 * It offers the three destinations that make sense from anywhere: the
 * portada, the account and the administration area.
 */
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-svh w-full max-w-page animate-in fade-in-0 flex-col justify-center gap-8 px-4 py-16 duration-500 ease-out sm:px-6">
      <BrandMark size={30} />
      <div className="flex flex-col gap-3">
        <p className="text-eyebrow-brand text-primary">Error 404</p>
        <h1 className="text-title-page text-foreground">
          No encontramos esta página
        </h1>
        <p className="max-w-measure text-lead text-muted-foreground">
          Puede que la dirección haya cambiado o que el contenido ya no esté
          disponible en esta edición.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button asChild className="min-h-11">
          <a href={RUTAS.publico.inicio}>Ir al inicio</a>
        </Button>
        <Button variant="outline" asChild className="min-h-11">
          <a href={RUTAS.cuenta.miCuenta}>Mi cuenta</a>
        </Button>
        <Button variant="ghost" asChild className="min-h-11">
          <a href={RUTAS.publico.informacion}>Información</a>
        </Button>
      </div>
    </main>
  );
}
