"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";

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
  const href = user ? "/inscripcion" : "/register";

  return (
    <Button asChild variant={variant} size={size} className={className}>
      <Link href={href}>Preinscribir equipo</Link>
    </Button>
  );
}
