"use client";

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  Loader2,
  Pencil,
  Trophy,
  Users,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InscripcionEditModal } from "../components/InscripcionEditModal";
import { useMyInscripcion } from "../hooks/useMyInscripcion";

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: typeof Clock }
> = {
  recibida: {
    label: "Recibida",
    color: "text-blue-600 bg-blue-100",
    icon: Clock,
  },
  en_revision: {
    label: "En revisión",
    color: "text-yellow-600 bg-yellow-100",
    icon: Clock,
  },
  observada: {
    label: "Observada",
    color: "text-orange-600 bg-orange-100",
    icon: AlertCircle,
  },
  validada: {
    label: "Validada",
    color: "text-green-600 bg-green-100",
    icon: CheckCircle2,
  },
  pago_pendiente: {
    label: "Pago pendiente",
    color: "text-amber-600 bg-amber-100",
    icon: Clock,
  },
  pagada: {
    label: "Pagada",
    color: "text-emerald-600 bg-emerald-100",
    icon: CheckCircle2,
  },
  confirmada: {
    label: "Confirmada",
    color: "text-green-600 bg-green-100",
    icon: CheckCircle2,
  },
  rechazada: {
    label: "Rechazada",
    color: "text-red-600 bg-red-100",
    icon: XCircle,
  },
};

export function ResponsableDashboardView() {
  const { data, isLoading, refetch } = useMyInscripcion();
  const [editOpen, setEditOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="size-8 animate-spin text-[#312e8e]" />
      </div>
    );
  }

  // No tiene inscripción aún
  if (!data) {
    return (
      <div className="space-y-6">
        <Card className="card-elevated">
          <CardHeader>
            <CardTitle className="text-xl text-[#17214b]">
              Bienvenido a Salesianos FEST 2026
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-start gap-3 rounded-xl border-2 border-[#f4c64e]/40 bg-[#fff9df] p-4">
              <AlertCircle className="size-5 shrink-0 mt-0.5 text-[#f4c64e]" />
              <div>
                <p className="font-bold text-[#17214b]">
                  Aún no tienes una inscripción registrada.
                </p>
                <p className="text-sm text-muted-foreground">
                  Preinscribe la nómina de tu promoción para las Olimpiadas
                  Deportivas Salesianas.
                </p>
              </div>
            </div>
            <Button
              asChild
              className="btn-brand-gradient btn-shine h-12 rounded-xl px-8 font-black"
            >
              <Link href="/inscripcion">
                Preinscribir mi equipo <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const cfg = STATUS_CONFIG[data.inscripcion.status] ?? STATUS_CONFIG.recibida;
  const Icon = cfg.icon;
  const isEditable = ![
    "validada",
    "pagada",
    "confirmada",
    "rechazada",
  ].includes(data.inscripcion.status);
  const totalIntegrantes = data.deportistas.length;
  const totalDisciplinas = new Set(
    data.equipos.map((equipo) => equipo.disciplinaId),
  ).size;
  const equiposById = new Map(
    data.equipos.map((equipo) => [equipo.id, equipo]),
  );

  return (
    <div className="space-y-6">
      <Card className="card-elevated">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl text-[#17214b]">
              <FileText className="size-5 text-[#312e8e]" /> Mi inscripción
            </CardTitle>
            {isEditable && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditOpen(true)}
                className="gap-2"
              >
                <Pencil className="size-4" /> Editar
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center gap-4">
            <div
              className={`flex size-14 items-center justify-center rounded-2xl ${cfg.color}`}
            >
              <Icon className="size-7" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Estado
              </p>
              <p className="text-2xl font-black text-[#17214b]">{cfg.label}</p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-[#f4f6fb] p-4">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Equipo
              </p>
              <p className="mt-1 text-xl font-black text-[#17214b]">
                {data.inscripcion.teamName}
              </p>
            </div>
            <div className="rounded-xl bg-[#f4f6fb] p-4">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Paquete
              </p>
              <p className="mt-1 text-xl font-black text-[#17214b]">
                S/{" "}
                {Number(data.inscripcion.paqueteMonto).toLocaleString("es-PE")}
              </p>
            </div>
            <div className="rounded-xl bg-[#f4f6fb] p-4">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Registrada
              </p>
              <p className="mt-1 text-xl font-black text-[#17214b]">
                {new Date(data.inscripcion.createdAt).toLocaleDateString(
                  "es-PE",
                )}
              </p>
            </div>
            <div className="rounded-xl bg-[#f4f6fb] p-4">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Integrantes
              </p>
              <p className="mt-1 text-xl font-black text-[#17214b]">
                {totalIntegrantes}{" "}
                {totalIntegrantes === 1 ? "registrado" : "registrados"}
              </p>
            </div>
            <div className="rounded-xl bg-[#f4f6fb] p-4">
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Deportes
              </p>
              <p className="mt-1 text-xl font-black text-[#17214b]">
                {totalDisciplinas}{" "}
                {totalDisciplinas === 1 ? "disciplina" : "disciplinas"}
              </p>
            </div>
          </div>

          {data.inscripcion.observacion && (
            <div className="flex items-start gap-3 rounded-xl border border-orange-300/50 bg-orange-50 p-4">
              <AlertCircle className="size-5 shrink-0 mt-0.5 text-orange-600" />
              <div>
                <p className="font-bold text-orange-800">
                  Observación del Comité
                </p>
                <p className="text-sm text-orange-700">
                  {data.inscripcion.observacion}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl text-[#17214b]">
            <Users className="size-5 text-[#312e8e]" /> Integrantes registrados
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.deportistas.length > 0 ? (
            <div className="divide-y divide-border/60 rounded-xl border border-[#312e8e]/10 bg-white">
              {data.deportistas.map((dep) => {
                const equiposAsignados = dep.equipoIds.flatMap((equipoId) => {
                  const equipo = equiposById.get(equipoId);
                  return equipo ? [equipo] : [];
                });

                return (
                  <div key={dep.id} className="space-y-3 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="font-black text-[#17214b]">
                          {dep.persona.apellidos}, {dep.persona.nombres}
                        </p>
                        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                          <span>
                            <span className="font-semibold">
                              {dep.persona.tipoDocumento}:
                            </span>{" "}
                            {dep.persona.numeroDocumento}
                          </span>
                          {dep.persona.telefono && (
                            <span>
                              <span className="font-semibold">Teléfono:</span>{" "}
                              {dep.persona.telefono}
                            </span>
                          )}
                          <span>
                            <span className="font-semibold">Rol:</span>{" "}
                            {dep.rolDisciplina}
                          </span>
                          {dep.shirtSize && (
                            <span>
                              <span className="font-semibold">Talla:</span>{" "}
                              {dep.shirtSize}
                            </span>
                          )}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className="w-fit shrink-0 text-xs"
                      >
                        {dep.acreditacion}
                      </Badge>
                    </div>

                    {equiposAsignados.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {equiposAsignados.map((equipo) => (
                          <Badge
                            key={equipo.id}
                            variant="secondary"
                            className="bg-[#312e8e]/10 text-[#312e8e]"
                          >
                            {equipo.disciplinaNombre} · {equipo.categoriaNombre}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex items-center justify-center rounded-xl border border-dashed border-[#312e8e]/20 p-6 text-muted-foreground">
              <Users className="mr-2 size-5 opacity-50" />
              <p className="text-sm italic">
                Aún no hay integrantes registrados.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Equipos y Deportistas */}
      {data.equipos.length > 0 && (
        <Card className="card-elevated">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl text-[#17214b]">
              <Trophy className="size-5 text-[#312e8e]" /> Deportes y equipos
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.equipos.map((equipo) => {
              const equipoDeportistas = data.deportistas.filter((d) =>
                d.equipoIds.includes(equipo.id),
              );
              return (
                <div
                  key={equipo.id}
                  className="rounded-xl border-2 border-[#312e8e]/10 bg-[#f4f6fb] overflow-hidden"
                >
                  {/* Equipo header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 sm:p-4 bg-[#312e8e]/05 border-b border-[#312e8e]/10">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant="outline"
                        className="bg-white font-bold text-[#312e8e] border-[#312e8e]/30 text-xs sm:text-sm"
                      >
                        {equipo.disciplinaNombre}
                      </Badge>
                      <Badge
                        variant="secondary"
                        className="bg-[#312e8e]/10 text-[#312e8e] border-0 text-xs sm:text-sm"
                      >
                        {equipo.categoriaNombre}
                      </Badge>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground sm:text-right">
                      {equipoDeportistas.length}{" "}
                      {equipoDeportistas.length === 1
                        ? "deportista"
                        : "deportistas"}
                    </span>
                  </div>

                  {/* Deportistas list */}
                  {equipoDeportistas.length > 0 ? (
                    <div className="divide-y divide-border/50">
                      {equipoDeportistas.map((dep, index) => (
                        <div
                          key={dep.id}
                          className="flex items-start sm:items-center justify-between gap-2 p-3 sm:p-4 bg-white hover:bg-slate-50/50 transition-colors"
                        >
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            {/* Index number */}
                            <span className="flex items-center justify-center size-6 sm:size-7 rounded-full bg-[#312e8e]/10 text-[#312e8e] text-xs font-bold shrink-0">
                              {index + 1}
                            </span>
                            <div className="min-w-0 flex-1">
                              <p className="font-bold text-sm sm:text-base text-[#17214b] truncate">
                                {dep.persona.apellidos}, {dep.persona.nombres}
                              </p>
                              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-0.5">
                                <span className="text-xs text-muted-foreground">
                                  <span className="font-medium">
                                    {dep.persona.tipoDocumento}:
                                  </span>{" "}
                                  {dep.persona.numeroDocumento}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  <span className="font-medium">
                                    {dep.rolDisciplina}
                                  </span>
                                </span>
                                {dep.shirtSize && (
                                  <span className="text-xs text-muted-foreground">
                                    <span className="font-medium">Talla:</span>{" "}
                                    {dep.shirtSize}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className="text-xs shrink-0 ml-2"
                          >
                            {dep.acreditacion}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center p-6 text-muted-foreground">
                      <Users className="size-5 mr-2 opacity-50" />
                      <p className="text-sm italic">
                        Sin deportistas asignados a este equipo
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      <InscripcionEditModal
        open={editOpen}
        onOpenChange={setEditOpen}
        inscripcion={data}
        onSuccess={() => refetch()}
      />
    </div>
  );
}
