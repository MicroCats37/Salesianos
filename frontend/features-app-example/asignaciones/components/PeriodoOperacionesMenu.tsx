"use client";

import {
  AlertTriangle,
  ArrowLeftRight,
  Loader2,
  MoreHorizontal,
  PlayCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export type PeriodoOperation =
  | "iniciar-gestion"
  | "marcar-erronea"
  | "cambiar-participacion";

interface PeriodoOperacionesMenuProps {
  periodoId: string;
  estado: string;
  isPending?: boolean;
  /** Disables the operations menu when the user does not belong to the area. */
  disabled?: boolean;
  onOperationSelect: (periodoId: string, operation: PeriodoOperation) => void;
}

function OperacionesMenuItem({
  label,
  icon: Icon,
  onSelect,
  disabled,
  isLoading,
}: {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  onSelect: () => void;
  disabled?: boolean;
  isLoading?: boolean;
}) {
  return (
    <DropdownMenuItem
      onSelect={onSelect}
      disabled={disabled || isLoading}
      className="gap-2 cursor-pointer"
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Icon className="h-4 w-4" />
      )}
      <span>{label}</span>
    </DropdownMenuItem>
  );
}

export function PeriodoOperacionesMenu({
  periodoId,
  estado,
  isPending,
  disabled,
  onOperationSelect,
}: PeriodoOperacionesMenuProps) {
  const handleOperation = (operation: PeriodoOperation) => {
    onOperationSelect(periodoId, operation);
  };

  if (estado === "CERRADO") {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1.5 text-xs px-2"
          disabled={isPending || disabled}
        >
          <MoreHorizontal className="h-3.5 w-3.5" />
          <span>Operaciones</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        {estado === "PENDIENTE" && (
          <OperacionesMenuItem
            label="Iniciar gestión"
            icon={PlayCircle}
            onSelect={() => handleOperation("iniciar-gestion")}
            disabled={isPending}
          />
        )}
        {estado === "EN_GESTION" && (
          <>
            <OperacionesMenuItem
              label="No corresponde a mi área"
              icon={AlertTriangle}
              onSelect={() => handleOperation("marcar-erronea")}
              disabled={isPending}
            />
            <DropdownMenuSeparator />
            <OperacionesMenuItem
              label="Cambiar participación"
              icon={ArrowLeftRight}
              onSelect={() => handleOperation("cambiar-participacion")}
              disabled={isPending}
            />
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
