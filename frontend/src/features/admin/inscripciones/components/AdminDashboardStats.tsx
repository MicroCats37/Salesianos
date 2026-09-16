"use client";

import {
  AlertCircle,
  CheckCircle2,
  Clock,
  ListChecks,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAllInscripciones } from "@/features/admin/inscripciones/hooks/useAllInscripciones";

export function AdminDashboardStats() {
  const { data, isLoading } = useAllInscripciones();

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  const counts = {
    recibida: items.filter((i) => i.inscripcion.status === "recibida").length,
    en_revision: items.filter((i) => i.inscripcion.status === "en_revision")
      .length,
    validada: items.filter((i) => i.inscripcion.status === "validada").length,
    observada: items.filter((i) => i.inscripcion.status === "observada").length,
    rechazada: items.filter((i) => i.inscripcion.status === "rechazada").length,
  };

  const stats = [
    {
      label: "Total inscripciones",
      value: total,
      icon: ListChecks,
      color: "text-[#312e8e] bg-[#312e8e]/10",
    },
    {
      label: "Recibidas",
      value: counts.recibida,
      icon: Clock,
      color: "text-blue-600 bg-blue-100",
    },
    {
      label: "En revisión",
      value: counts.en_revision,
      icon: AlertCircle,
      color: "text-yellow-600 bg-yellow-100",
    },
    {
      label: "Validadas",
      value: counts.validada,
      icon: CheckCircle2,
      color: "text-green-600 bg-green-100",
    },
    {
      label: "Observadas",
      value: counts.observada,
      icon: AlertCircle,
      color: "text-orange-600 bg-orange-100",
    },
    {
      label: "Rechazadas",
      value: counts.rechazada,
      icon: XCircle,
      color: "text-red-600 bg-red-100",
    },
  ];

  if (isLoading) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        Cargando estadísticas...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label} className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div
                className={`flex size-12 items-center justify-center rounded-xl ${s.color}`}
              >
                <s.icon className="size-6" />
              </div>
              <div>
                <p className="text-3xl font-black text-[#17214b]">{s.value}</p>
                <p className="text-sm text-muted-foreground">{s.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
