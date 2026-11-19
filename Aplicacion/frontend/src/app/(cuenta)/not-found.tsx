import { Button } from "@/components/ui/button";

/**
 * The 404 of this group.
 */
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[60svh] w-full max-w-[720px] flex-col justify-center gap-6 px-4 py-12 sm:px-6">
      <div className="flex flex-col gap-3">
        <p className="text-eyebrow-brand text-primary">Error 404</p>
        <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
          No encontramos este registro
        </h1>
        <p className="text-muted-foreground">
          Puede que el registro no exista o que ya no esté disponible en esta
          edición.
        </p>
      </div>
      <Button variant="outline" asChild>
        <a href="/">Ir al inicio</a>
      </Button>
    </main>
  );
}
