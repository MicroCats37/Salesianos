"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";

interface PreinscribirButtonProps {
  variant?: React.ComponentProps<typeof Button>["variant"];
  size?: React.ComponentProps<typeof Button>["size"];
  className?: string;
}

export function PreinscribirButton({
  variant,
  size,
  className,
}: PreinscribirButtonProps) {
  const user = useAuthUser();
  const href = user ? RUTAS.cuenta.inscripcion : RUTAS.auth.registro;

  return (
    <Button
      asChild
      variant={variant}
      size={size}
      className={cn("min-h-11", className)}
    >
      <Link href={href}>Preinscribir equipo</Link>
    </Button>
  );
}
