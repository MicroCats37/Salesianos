import { Bell } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { NotificacionSummary } from "../services/notificacion.service";

export interface NotificationSummaryCardsProps {
  /** Summary counts from useNotificacionSummary. May be null while loading or on error. */
  summary: NotificacionSummary | null | undefined;
  /** Set to true while the summary query is pending. Shows skeleton cards. */
  isLoading?: boolean;
}

/**
 * Displays notification counts as a strip of summary cards.
 * Gracefully handles loading (skeleton), null/undefined (no crash), and zero counts.
 */
export function NotificationSummaryCards({
  summary,
  isLoading = false,
}: NotificationSummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="flex gap-4 flex-wrap">
        <SummaryCardSkeleton />
        <SummaryCardSkeleton />
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="flex gap-4 flex-wrap">
      <SummaryCard
        label="Total"
        value={summary.total}
        icon={<Bell className="h-4 w-4" />}
      />
      <SummaryCard
        label="Sin abrir"
        value={summary.sin_leer}
        icon={<Bell className="h-4 w-4 text-destructive" />}
        highlight
      />
    </div>
  );
}

interface SummaryCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  highlight?: boolean;
}

function SummaryCard({ label, value, icon, highlight }: SummaryCardProps) {
  return (
    <div
      className={[
        "flex items-center gap-3 rounded-xl border bg-card px-4 py-2 text-sm shadow-sm",
        highlight
          ? "border-destructive/30 bg-destructive/5"
          : "border-border/80 bg-card",
      ].join(" ")}
    >
      {icon}
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground font-medium">
          {label}
        </span>
        <span
          className={[
            "text-lg font-semibold leading-none",
            highlight ? "text-destructive" : "text-foreground",
          ].join(" ")}
        >
          {value}
        </span>
      </div>
    </div>
  );
}

function SummaryCardSkeleton() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border/80 bg-card px-4 py-2 shadow-sm">
      <Skeleton className="h-8 w-8 rounded-md" />
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-5 w-8" />
      </div>
    </div>
  );
}
