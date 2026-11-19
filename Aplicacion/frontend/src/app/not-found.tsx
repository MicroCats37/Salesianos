import { BrandMark } from "@/components/brand/BrandMark";
import { Button } from "@/components/ui/button";

/**
 * The global 404.
 *
 * It offers the three destinations that make sense from anywhere: the
 * portada, the account and the administration area.
 */
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-svh max-w-[640px] flex-col justify-center gap-8 px-4 py-16 sm:px-6">
      <BrandMark size={30} />
      <div className="flex flex-col gap-3">
        <p className="text-eyebrow-brand text-primary">Error 404</p>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          No encontramos esta página
        </h1>
        <p className="text-muted-foreground">
          Puede que la dirección haya cambiado o que el contenido ya no esté
          disponible en esta edición.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <a href="/">Ir al inicio</a>
        </Button>
        <Button variant="outline" asChild>
          <a href="/mi-cuenta">Mi cuenta</a>
        </Button>
        <Button variant="ghost" asChild>
          <a href="/informacion">Información</a>
        </Button>
      </div>
    </main>
  );
}
