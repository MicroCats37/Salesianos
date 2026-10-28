"use client";

import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  CalendarDays,
  ClipboardList,
  CreditCard,
  QrCode,
  RefreshCw,
  ScanLine,
  Ticket,
  Trophy,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RichEmptyState } from "@/components-app/pages/RichEmptyState";
import { cn } from "@/lib/utils";
import { useAdminResumen } from "../hooks/useAdminResumen";
import {
  formatearFecha,
  resumenAlertas,
  resumenKpis,
} from "../utils/admin.resumen.utils";
import { AdminAccessDenied } from "./AdminAccessDenied";
import { AdminAlertList } from "./AdminAlertList";
import { AdminKpiCard } from "./AdminKpiCard";
import { AdminPageHeader } from "./AdminPageHeader";

/** Icon of every metric tile of the overview. */
const KPI_ICONS: Record<string, LucideIcon> = {
  inscripciones: ClipboardList,
  pagos: CreditCard,
  cupos: Ticket,
  pases: Ticket,
  equipos: Trophy,
  participantes: Users,
  acreditaciones: QrCode,
  accesos: ScanLine,
};

/**
 * Operational overview of the active event.
 *
 * Every number comes from the backend (`GET /administracion/resumen`); this
 * component only groups and formats it. The panel is responsive by design:
 * the tiles stack in a single column on mobile and the attention lists turn
 * into stacked cards.
 */
export function AdminOverview() {
  const { data, isPending, isError, error, refetch } = useAdminResumen();

  if (isError) {
    if (error?.status === 403) {
      return <AdminAccessDenied message={error.message} />;
    }

    return (
      <AdminErrorState
        message={error?.message ?? "No se pudo cargar el resumen operativo."}
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  if (isPending) {
    return <AdminOverviewSkeleton />;
  }

  const resumen = data?.success && data?.data ? data.data : null;

  if (!resumen) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-10">
        <RichEmptyState
          icon={<ClipboardList className="h-9 w-9" />}
          iconBgColor="bg-white"
          iconTextColor="text-slate-400"
          title="Sin resumen disponible"
          description="El servidor no devolvió métricas del evento activo. Vuelve a intentarlo en unos segundos."
          actionLabel="Reintentar"
          onAction={() => {
            void refetch();
          }}
        />
      </div>
    );
  }

  const kpis = resumenKpis(resumen);
  const alertas = resumenAlertas(resumen);
  const { evento } = resumen;
  /**
   * The last tile spans TWO columns only when the grid would otherwise leave
   * a hole: with a multiple of four tiles every row is complete.
   */
  const ultimoOcupaDos = kpis.length % 4 === 3;

  return (
    <div className="flex min-h-svh w-full flex-col text-slate-900">
      <AdminPageHeader
        eyebrow="Administración operativa"
        title={evento.nombre}
        size="hero"
        badges={
          <>
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10px] font-black uppercase tracking-wider",
                evento.esta_activo
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-slate-50 text-slate-600",
              )}
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  evento.esta_activo ? "bg-emerald-500" : "bg-slate-400",
                )}
              />
              {evento.esta_activo ? "Evento activo" : "Evento inactivo"}
            </span>

            <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/70 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-slate-600">
              <CalendarDays className="size-3" />
              {formatearFecha(evento.fecha_inicio)} —{" "}
              {formatearFecha(evento.fecha_fin)}
            </span>

            {evento.fecha_limite_modificacion ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-amber-700">
                Modificaciones hasta el{" "}
                {formatearFecha(evento.fecha_limite_modificacion)}
              </span>
            ) : null}

            <span className="inline-flex items-center gap-2">
              <span className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">
                Estado de edición
              </span>
              <span
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wider",
                  evento.puede_modificar
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-rose-200 bg-rose-50 text-rose-700",
                )}
              >
                {evento.puede_modificar ? "Editable" : "Cerrada"}
              </span>
            </span>
          </>
        }
      />

      <section className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 sm:py-10 lg:px-10">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi, index) => {
            const Icon = KPI_ICONS[kpi.id] ?? ClipboardList;

            return (
              <AdminKpiCard
                key={kpi.id}
                kpi={kpi}
                icon={Icon}
                className={
                  index === kpis.length - 1 && ultimoOcupaDos
                    ? "sm:col-span-2 xl:col-span-2"
                    : undefined
                }
              />
            );
          })}
        </div>

        <div className="mt-8">
          <header className="mb-4">
            <p className="text-eyebrow-brand">Alertas operativas</p>
            <h2 className="mt-1 text-xl font-black tracking-tight text-[#17214b] sm:text-2xl">
              Requiere atención
            </h2>
          </header>

          {alertas.length === 0 ? (
            <div className="rounded-3xl border border-emerald-200 bg-emerald-50/70 p-6 text-center">
              <p className="text-sm font-bold text-emerald-800">
                Sin pendientes operativos
              </p>
              <p className="mt-1 text-xs text-emerald-700/80">
                No hay inscripciones por revisar, pagos detenidos ni cupos sin
                asignar en este momento.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {alertas.map((group) => (
                <AdminAlertList key={group.id} group={group} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

/**
 * Inline error state with a retry action.
 *
 * The administration area NEVER relies on a toast alone: the failure stays
 * visible in the page (`contract/api-wrapper-presenter-contract.md` §8.3 of
 * the admin surface).
 */
function AdminErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col items-center gap-4 px-4 py-16 sm:px-6">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-rose-200 bg-rose-50 text-rose-600">
        <AlertCircle className="size-7" />
      </div>
      <div className="space-y-1 text-center">
        <h2 className="text-lg font-black tracking-tight text-slate-900">
          No se pudo cargar el resumen
        </h2>
        <p className="text-sm leading-relaxed text-slate-600">{message}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        onClick={onRetry}
        className="btn-brand-gradient btn-shine h-10 gap-2 rounded-full px-5 text-xs font-black uppercase tracking-wider"
      >
        <RefreshCw className="h-3.5 w-3.5" />
        Reintentar
      </Button>
    </div>
  );
}

/** Skeleton of the overview — mirrors the shape of the real tiles. */
const SKELETON_TILES = [
  "inscripciones",
  "pagos",
  "cupos",
  "pases",
  "participantes",
  "equipos",
  "acreditaciones",
  "accesos",
];

const SKELETON_GROUPS = ["alertas-1", "alertas-2"];

const SKELETON_ITEMS = ["item-1", "item-2", "item-3"];

function AdminOverviewSkeleton() {
  const ultimoOcupaDos = SKELETON_TILES.length % 4 === 3;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-10">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {SKELETON_TILES.map((tile, index) => (
          <div
            key={tile}
            className={cn(
              "card-elevated p-6",
              index === SKELETON_TILES.length - 1 &&
                ultimoOcupaDos &&
                "sm:col-span-2 xl:col-span-2",
            )}
          >
            <Skeleton className="h-3 w-24" />
            <Skeleton className="mt-4 h-8 w-32" />
            <Skeleton className="mt-4 h-3 w-40" />
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        {SKELETON_GROUPS.map((group) => (
          <div key={group} className="card-elevated p-6">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="mt-2 h-3 w-64" />
            <div className="mt-4 flex flex-col gap-2">
              {SKELETON_ITEMS.map((item) => (
                <Skeleton key={item} className="h-14 w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
