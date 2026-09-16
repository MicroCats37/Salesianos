"use client";

import { ChevronDown, ChevronRight, ListChecks } from "lucide-react";
import { useState } from "react";
import { EmptyState } from "@/components/emptyState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  type AdminInscripcionListItem,
  type AdminJugadorItem,
  useAllInscripciones,
} from "../hooks/useAllInscripciones";
import { StatusChangeDialog } from "./StatusChangeDialog";

const STATUS_LABELS: Record<string, string> = {
  recibida: "Recibida",
  en_revision: "En revisión",
  observada: "Observada",
  validada: "Validada",
  pago_pendiente: "Pago pendiente",
  pagada: "Pagada",
  confirmada: "Confirmada",
  rechazada: "Rechazada",
};

const STATUS_COLORS: Record<string, string> = {
  recibida: "bg-blue-100 text-blue-800",
  en_revision: "bg-yellow-100 text-yellow-800",
  observada: "bg-orange-100 text-orange-800",
  validada: "bg-green-100 text-green-800",
  rechazada: "bg-red-100 text-red-800",
};

function JugadorCard({ jugador }: { jugador: AdminJugadorItem }) {
  return (
    <div className="rounded-md border bg-muted/40 p-3 text-sm space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">
          {jugador.nombre} {jugador.apellido}
        </span>
        <Badge variant="outline" className="text-xs">
          {jugador.rolDisciplina}
        </Badge>
      </div>
      <div className="text-muted-foreground text-xs">
        {jugador.tipoDocumento} {jugador.numeroDocumento}
        {jugador.telefono && ` · Tel: ${jugador.telefono}`}
        {jugador.whatsapp && ` · WA: ${jugador.whatsapp}`}
      </div>
      {jugador.equipos.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {jugador.equipos.map((eq) => (
            <Badge
              key={`${eq.disciplinaNombre}-${eq.categoriaNombre}`}
              variant="secondary"
              className="text-xs"
            >
              {eq.disciplinaNombre} ({eq.categoriaNombre})
            </Badge>
          ))}
        </div>
      )}
      {jugador.shirtSize && (
        <div className="text-xs text-muted-foreground">
          Camiseta: {jugador.shirtSize}
        </div>
      )}
    </div>
  );
}

export function InscripcionListTable() {
  const { data, isLoading } = useAllInscripciones();
  const [selected, setSelected] = useState<AdminInscripcionListItem | null>(
    null,
  );
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleExpanded = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="text-center py-12 text-muted-foreground">Cargando...</div>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <EmptyState
        title="Sin inscripciones"
        description="No hay inscripciones registradas todavía."
      />
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Inscripciones ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Desktop table */}
          <div className="hidden md:block overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-2 w-8"></th>
                  <th className="text-left p-2">Responsable</th>
                  <th className="text-left p-2">DNI</th>
                  <th className="text-left p-2">Equipos</th>
                  <th className="text-left p-2">Estado</th>
                  <th className="text-left p-2">Acción</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const isExpanded = expanded.has(item.inscripcion.id);
                  const hasJugadores = item.jugadores.length > 0;
                  return (
                    <>
                      <tr key={item.inscripcion.id} className="border-b">
                        <td className="p-2">
                          {hasJugadores ? (
                            <button
                              type="button"
                              onClick={() =>
                                toggleExpanded(item.inscripcion.id)
                              }
                              className="p-1 rounded hover:bg-muted"
                              aria-label={isExpanded ? "Contraer" : "Expandir"}
                            >
                              {isExpanded ? (
                                <ChevronDown className="size-4" />
                              ) : (
                                <ChevronRight className="size-4" />
                              )}
                            </button>
                          ) : (
                            <span className="block w-6" />
                          )}
                        </td>
                        <td className="p-2">
                          {item.userNombre} {item.userApellido}
                        </td>
                        <td className="p-2">{item.userDni}</td>
                        <td className="p-2">
                          {item.equiposCount} ({item.jugadoresCount} jugadores)
                        </td>
                        <td className="p-2">
                          <Badge
                            className={
                              STATUS_COLORS[item.inscripcion.status] ?? ""
                            }
                          >
                            {STATUS_LABELS[item.inscripcion.status] ??
                              item.inscripcion.status}
                          </Badge>
                        </td>
                        <td className="p-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelected(item)}
                          >
                            Cambiar estado
                          </Button>
                        </td>
                      </tr>
                      {isExpanded && hasJugadores && (
                        <tr key={`${item.inscripcion.id}-detail`}>
                          <td colSpan={6} className="p-3 bg-muted/20">
                            <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
                              <ListChecks className="size-3" />
                              Jugadores
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                              {item.jugadores.map((j) => (
                                <JugadorCard
                                  key={j.numeroDocumento}
                                  jugador={j}
                                />
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-3">
            {items.map((item) => {
              const isExpanded = expanded.has(item.inscripcion.id);
              const hasJugadores = item.jugadores.length > 0;
              return (
                <div
                  key={item.inscripcion.id}
                  className="rounded-lg border p-4 space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <p className="font-medium text-sm">
                        {item.userNombre} {item.userApellido}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.userDni}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {item.equiposCount} equipos ({item.jugadoresCount}{" "}
                        jugadores)
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge
                        className={
                          STATUS_COLORS[item.inscripcion.status] ??
                          "bg-gray-100"
                        }
                      >
                        {STATUS_LABELS[item.inscripcion.status] ??
                          item.inscripcion.status}
                      </Badge>
                      {hasJugadores && (
                        <button
                          type="button"
                          onClick={() => toggleExpanded(item.inscripcion.id)}
                          className="text-xs flex items-center gap-1 text-muted-foreground hover:text-foreground"
                        >
                          {isExpanded ? "Ocultar" : "Ver"} jugadores
                          {isExpanded ? (
                            <ChevronDown className="size-3" />
                          ) : (
                            <ChevronRight className="size-3" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelected(item)}
                      className="flex-1"
                    >
                      Cambiar estado
                    </Button>
                  </div>
                  {isExpanded && hasJugadores && (
                    <div className="space-y-2 pt-2 border-t">
                      <p className="text-xs font-medium text-muted-foreground">
                        Jugadores
                      </p>
                      <div className="space-y-2">
                        {item.jugadores.map((j) => (
                          <JugadorCard key={j.numeroDocumento} jugador={j} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
      {selected && (
        <StatusChangeDialog
          inscripcion={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}
