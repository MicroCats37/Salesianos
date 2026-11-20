import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface FormGridProps {
  children: ReactNode;
  className?: string;
}

export function FormGrid({ children, className }: FormGridProps) {
  return (
    <div className={cn("grid grid-cols-1 gap-4 md:grid-cols-12", className)}>
      {children}
    </div>
  );
}
