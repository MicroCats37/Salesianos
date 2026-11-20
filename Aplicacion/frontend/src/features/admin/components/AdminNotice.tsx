import { Info } from "lucide-react";
import type { ReactNode } from "react";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { cn } from "@/lib/utils";

export interface AdminNoticeProps {
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * AdminNotice - a permanent statement about the state of a block.
 *
 * It exists for the cases where the operator must know something BEFORE
 * reading the block: that a surface is read-only, that the data source is
 * not connected yet, that an action belongs to another section. A notice
 * that appears and disappears with the data is a toast; a notice that stays
 * is information.
 */
export function AdminNotice({
  title,
  children,
  className,
}: AdminNoticeProps) {
  return (
    <Alert className={cn("px-4 py-3", className)}>
      <Info className="size-4" aria-hidden="true" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  );
}
