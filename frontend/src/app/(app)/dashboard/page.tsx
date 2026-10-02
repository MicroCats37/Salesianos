"use client";

import {
  ArrowRight,
  CalendarDays,
  ChevronRight,
  CircleUserRound,
  Clock4,
  CreditCard,
  GraduationCap,
  Package,
  PackageOpen,
  PartyPopper,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";
import {
  getMisInscripciones,
  type InscripcionOut,
} from "@/features/inscripciones/services/inscripcion.service";
import { cn } from "@/lib/utils";

type EstadoInscripcion =
  | "CONFIRMADA"
  | "PENDIENTE"
  | "PAGO_PENDIENTE"
  | "PAGADA"
  | "CANCELADA"
  | string;

const ESTADO_META: Record<
  string,
  {
    label: string;
    description: string;
    pillClass: string;
    accentClass: string;
    stepIndex: number; // 1..4 to illustrate flow progress
    icon: React.ComponentType<{ className?: string }>;
  }
> = {
  PENDIENTE: {
    label: "Pendiente",
    description: "Tu inscripcion esta creada. Falta elegir paquete y equipos.",
    pillClass: "bg-amber-100 text-amber-800 border-amber-200",
    accentClass: "from-amber-100/80 to-amber-50",
    stepIndex: 2,
    icon: Clock4,
  },
  PAGO_PENDIENTE: {
    label: "Pago Pendiente",
    description:
      "Tu inscripcion esta guardando confirmacion de pago. Completa el pago para que sea procesada.",
    pillClass: "bg-orange-100 text-orange-800 border-orange-200",
    accentClass: "from-orange-100/80 to-rose-50",
    stepIndex: 3,
    icon: CreditCard,
  },
  PAGADA: {
    label: "Pagada",
    description: "Pago confirmado. Esperamos validacion del Comite.",
    pillClass: "bg-sky-100 text-sky-800 border-sky-200",
    accentClass: "from-sky-100/80 to-indigo-50",
    stepIndex: 4,
    icon: ShieldCheck,
  },
  CONFIRMADA: {
    label: "Confirmada",
    description: "Inscripcion validada. Ya puedes inscribir a las personas.",
    pillClass: "bg-emerald-100 text-emerald-800 border-emerald-200",
    accentClass: "from-emerald-100/80 to-emerald-50",
    stepIndex: 4,
    icon: PartyPopper,
  },
  CANCELADA: {
    label: "Cancelada",
    description: "Inscripcion cancelada. Contacta al Comite para mas detalles.",
    pillClass: "bg-rose-100 text-rose-800 border-rose-200",
    accentClass: "from-rose-100/80 to-rose-50",
    stepIndex: 0,
    icon: ShieldCheck,
  },
};

const FLOW_STEPS = [
  {
    label: "Crear inscripcion",
    description: "Promocion, paquete y equipos.",
    icon: GraduationCap,
  },
  {
    label: "Validar por el Comite",
    description: "Tu inscripcion es revisada por el Comite Organizador.",
    icon: ShieldCheck,
  },
  {
    label: "Completar el pago",
    description: "Una vez validada, pagas con izipay.",
    icon: CreditCard,
  },
  {
    label: "Inscribir personas",
    description: "Agregas jugadores desde el detalle de la inscripcion.",
    icon: CircleUserRound,
  },
];

function FlowProgress({ estado }: { estado: EstadoInscripcion }) {
  const meta = ESTADO_META[estado];
  const currentStep = meta?.stepIndex ?? 1;
  return (
    <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {FLOW_STEPS.map((step, idx) => {
        const Icon = step.icon;
        const stepNumber = idx + 1;
        const isCompleted = stepNumber < currentStep;
        const isCurrent = stepNumber === currentStep;
        return (
          <li
            key={step.label}
            className={cn(
              "relative flex flex-col gap-1 rounded-2xl border p-4 transition-all",
              isCompleted
                ? "border-emerald-200 bg-emerald-50/70"
                : isCurrent
                  ? "border-amber-300 bg-amber-50/80 shadow-sm"
                  : "border-slate-200 bg-white",
            )}
          >
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full text-sm font-black",
                  isCompleted
                    ? "bg-emerald-500 text-white"
                    : isCurrent
                      ? "bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow"
                      : "bg-slate-100 text-slate-400",
                )}
              >
                {isCompleted ? <ShieldCheck className="size-4" /> : stepNumber}
              </div>
              <span
                className={cn(
                  "text-[10px] font-black uppercase tracking-wider",
                  isCurrent
                    ? "text-amber-700"
                    : isCompleted
                      ? "text-emerald-700"
                      : "text-slate-400",
                )}
              >
                Paso {stepNumber}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Icon className="size-4" />
              {step.label}
            </div>
            <p className="text-xs leading-relaxed text-slate-500">
              {step.description}
            </p>
          </li>
        );
      })}
    </ol>
  );
}

function InscripcionCard({
  inscripcion,
  onClick,
}: {
  inscripcion: InscripcionOut;
  onClick: () => void;
}) {
  const meta = ESTADO_META[inscripcion.estado];
  const Icon = meta?.icon ?? ShieldCheck;
  const accent = meta?.accentClass ?? "from-slate-100/80 to-white";
  const pillClass =
    meta?.pillClass ?? "bg-slate-100 text-slate-700 border-slate-200";

  const equiposCount = inscripcion.cantidad_equipos ?? 0;
  const participantesCount = inscripcion.cantidad_participantes ?? 0;
  const paqueteNombre = inscripcion.paquete_nombre ?? null;
  const promocionNombre = inscripcion.promocion_nombre ?? null;

  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex w-full flex-col gap-4 overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 text-left shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
    >
      <div
        className={cn(
          "pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br opacity-60 transition-opacity group-hover:opacity-90",
          accent,
        )}
      />
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/80 shadow-md backdrop-blur">
            <PackageOpen className="size-5 text-[#312e8e]" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
              Inscripcion
            </p>
            <p className="truncate font-black text-slate-900">
              #{inscripcion.id.slice(0, 8)}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              Creada el{" "}
              {new Date(inscripcion.created_at).toLocaleDateString("es-PE", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wider",
            pillClass,
          )}
        >
          <Icon className="size-3.5" />
          {meta?.label ?? inscripcion.estado}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-slate-700">
        {meta?.description ??
          "Consulta al Comite para conocer el detalle de tu inscripcion."}
      </p>

      {(paqueteNombre || promocionNombre) && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
          {paqueteNombre && (
            <span className="inline-flex items-center gap-1">
              <PackageOpen className="size-3.5" />
              <span className="font-semibold text-slate-700">{paqueteNombre}</span>
            </span>
          )}
          {promocionNombre && (
            <span className="inline-flex items-center gap-1">
              <GraduationCap className="size-3.5" />
              <span className="font-semibold text-slate-700">
                {promocionNombre}
              </span>
            </span>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-2 border-t border-slate-100 pt-3 text-xs">
        <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
          <Users className="size-3.5 text-slate-500" />
          <div className="flex flex-col">
            <span className="font-black text-slate-900">{equiposCount}</span>
            <span className="text-[10px] uppercase tracking-wider text-slate-500">
              equipos
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
          <CircleUserRound className="size-3.5 text-slate-500" />
          <div className="flex flex-col">
            <span className="font-black text-slate-900">
              {participantesCount}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-slate-500">
              jugadores
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-sm">
        <span className="font-semibold text-slate-500">
          Ver detalle de la inscripcion
        </span>
        <span className="inline-flex items-center gap-1 text-sm font-black uppercase tracking-wider text-[#312e8e] transition-colors group-hover:text-[#25236f]">
          Continuar
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </button>
  );
}

function EmptyState({ onCreateNew }: { onCreateNew: () => void }) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-dashed border-amber-300 bg-gradient-to-br from-amber-50 via-white to-rose-50 p-10 text-center shadow-sm">
      <div className="absolute -right-12 -top-12 h-44 w-44 rounded-full bg-amber-200/40 blur-3xl" />
      <div className="absolute -bottom-16 -left-16 h-44 w-44 rounded-full bg-rose-200/40 blur-3xl" />
      <div className="relative mx-auto max-w-xl space-y-5">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-lg">
          <Sparkles className="size-7" />
        </div>
        <div className="space-y-2">
          <p className="text-[10px] font-black uppercase tracking-[0.35em] text-amber-700">
            Bienvenido a Salesianos FEST
          </p>
          <h2 className="text-3xl font-black tracking-tight text-slate-900">
            Aun no tienes inscripciones
          </h2>
          <p className="text-sm leading-relaxed text-slate-600">
            Empieza creando una inscripcion: elige promocion, paquete y
            registra a tus equipos. Despues de validar el pago podras inscribir
            a las personas desde el detalle.
          </p>
        </div>
        <Button
          type="button"
          onClick={onCreateNew}
          className="btn-brand-gradient btn-shine h-12 rounded-full px-8 text-sm font-black uppercase tracking-widest shadow-lg"
        >
          Crear primera inscripcion
          <ArrowRight className="size-4" />
        </Button>
        <div className="flex items-center justify-center gap-2 pt-2 text-xs text-slate-500">
          <CalendarDays className="size-3.5" />
          Paso 1 de 4. Toma 3 minutos.
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const user = useAuthUser();
  const router = useRouter();
  const [inscripciones, setInscripciones] = useState<InscripcionOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchInscripciones() {
      try {
        const res = await getMisInscripciones();
        if (res.success && res.data) {
          setInscripciones(res.data);
        } else {
          setError(res.error?.message ?? "Error al cargar inscripciones");
        }
      } catch {
        setError("Error de conexion");
      } finally {
        setLoading(false);
      }
    }
    fetchInscripciones();
  }, []);

  return (
    <div className="flex min-h-svh w-full flex-col bg-[linear-gradient(180deg,#f6f4ee_0%,#ffffff_30%,#ffffff_100%)] text-slate-900">
      {/* Brand hero */}
      <section className="relative overflow-hidden border-b border-slate-200/60 bg-gradient-to-br from-[#f6f4ee] via-white to-[#eef1f8]">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-amber-300/40 blur-3xl" />
        <div className="pointer-events-none absolute -left-24 bottom-0 h-72 w-72 rounded-full bg-cyan-300/40 blur-3xl" />
        <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-10 sm:px-6 lg:px-10">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-2">
              <p className="text-[10px] font-black uppercase tracking-[0.35em] text-[#312e8e]">
                Salesianos FEST 2026
              </p>
              <h1 className="text-3xl font-black tracking-tight text-[#17214b] sm:text-4xl">
                Hola, {user?.nombres?.split(" ")[0] ?? "equipo"}!
              </h1>
              <p className="max-w-2xl text-sm leading-relaxed text-[#17214b]/80">
                Aqui encontraras el estado de tus inscripciones, los equipos
                inscritos y los pasos que faltan para que tu delegacion quede
                completa antes del 21 de noviembre.
              </p>
            </div>
            <Button
              type="button"
              onClick={() => router.push("/inscripcion")}
              className="btn-brand-gradient btn-shine h-12 w-full rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg sm:w-auto"
            >
              Crear Inscripcion
              <ArrowRight className="size-4" />
            </Button>
          </div>

          {/* Flow diagram */}
          <div className="space-y-3">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]/70">
              Como funciona
            </p>
            <FlowProgress estado={inscripciones[0]?.estado ?? "PENDIENTE"} />
          </div>
        </div>
      </section>

      {/* Inscripciones */}
      <section className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 lg:px-10">
        <div className="overflow-hidden rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200/70 sm:p-8">
          <header className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
                Panel
              </p>
              <h2 className="text-2xl font-black tracking-tight text-[#17214b]">
                Mis Inscripciones
              </h2>
              <p className="text-sm text-[#17214b]/70">
                Cada tarjeta muestra el estado, que falta y el siguiente paso.
              </p>
            </div>
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-[#312e8e] hover:underline"
            >
              Ver el festival
              <ChevronRight className="size-4" />
            </Link>
          </header>

          {loading && (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-slate-500">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-[#312e8e]" />
              <p className="text-xs uppercase tracking-wider text-slate-400">
                Cargando inscripciones...
              </p>
            </div>
          )}

          {!loading && error && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-center text-sm text-rose-700">
              {error}
            </div>
          )}

          {!loading && !error && inscripciones.length === 0 && (
            <EmptyState onCreateNew={() => router.push("/inscripcion")} />
          )}

          {!loading && !error && inscripciones.length > 0 && (
            <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {inscripciones.map((insc) => (
                <InscripcionCard
                  key={insc.id}
                  inscripcion={insc}
                  onClick={() =>
                    router.push(`/dashboard/inscripcion/${insc.id}`)
                  }
                />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
