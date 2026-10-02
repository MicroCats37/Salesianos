"use client";

import { type LucideIcon } from "lucide-react";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface LiquidacionDetalleCompletaProps {
  item?: any;
  isLoading?: boolean;
  isError?: boolean;
  onBack?: () => void;
  kindLabel: string;
  kindIcon: LucideIcon;
}

export function LiquidacionDetalleCompleta({
  item,
  isLoading,
  isError,
  onBack,
  kindLabel,
  kindIcon: Icon,
}: LiquidacionDetalleCompletaProps) {
  if (isLoading) {
    return <div className="p-8 text-center">Cargando...</div>;
  }

  if (isError) {
    return (
      <div className="p-8 text-center text-red-500">
        Error al cargar los detalles
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Icon className="h-6 w-6" />
        <h2 className="text-xl font-bold">{kindLabel}</h2>
      </div>
      {item ? (
        <pre className="overflow-auto rounded bg-gray-100 p-4 text-xs">
          {JSON.stringify(item, null, 2)}
        </pre>
      ) : (
        <p className="text-gray-500">No hay datos disponibles</p>
      )}
      {onBack && (
        <button
          onClick={onBack}
          className="rounded bg-gray-200 px-4 py-2 hover:bg-gray-300"
        >
          Volver
        </button>
      )}
    </div>
  );
}

export function kindLabel(codigo?: string): string | undefined {
  return codigo;
}
