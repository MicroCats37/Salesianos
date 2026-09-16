"use client";

import { Loader2, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useLogout } from "@/features/auth/hooks/useLogout";

interface LogoutButtonProps {
  className?: string;
}

export function LogoutButton({ className }: LogoutButtonProps) {
  const router = useRouter();
  const logout = useLogout();

  const handleLogout = () => {
    if (logout.isPending) return;
    logout.mutate(undefined, {
      onSettled: () => {
        router.push("/");
        router.refresh();
      },
    });
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={logout.isPending}
      className={`flex w-full items-center gap-2 text-destructive ${className ?? ""}`}
    >
      {logout.isPending ? (
        <Loader2 className="size-4 animate-spin" />
      ) : (
        <LogOut className="size-4" />
      )}
      <span className="group-data-[collapsible=icon]:hidden">
        {logout.isPending ? "Cerrando..." : "Cerrar sesión"}
      </span>
    </button>
  );
}
