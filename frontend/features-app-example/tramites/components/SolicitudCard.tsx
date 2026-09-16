/**
 * SolicitudCard — card component for Solicitud list display.
 * Shows key solicitud fields with token-based badges and clickable navigation.
 */
"use client";

import {
  Briefcase,
  Calendar,
  Eye,
  Mail,
  Paperclip,
  Printer,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  ESTADO_SOLICITUD,
  type EstadoSolicitud,
  PRIORIDAD_SOLICITUD,
  type PrioridadSolicitud,
} from "@/shared/constants/tramite.tokens";
import type { SolicitudItem } from "../schemas/tramite.schema";
import { PrintPreviewModal } from "./PrintPreviewModal";
import { buildSolicitudPrintHTML } from "./printExpediente";
import { SolicitudPrintPreview } from "./SolicitudPrintPreview";

/** Safe accessor for tipo_documento which may be a string or {id,nombre,descripcion} object. */
function getTipoDocumentoLabel(td: unknown): string {
  if (!td) return "—";
  if (typeof td === "object" && "nombre" in (td as object)) {
    return (td as { nombre: string }).nombre;
  }
  if (typeof td === "string") return td;
  return "—";
}

interface SolicitudCardProps {
  item: SolicitudItem;
  onClick?: () => void;
}

export function SolicitudCard({ item, onClick: _onClick }: SolicitudCardProps) {
  const router = useRouter();

  const [printOpen, setPrintOpen] = useState(false);
  const [printHtml, setPrintHtml] = useState("");
  const [obsOpen, setObsOpen] = useState(false);

  const handlePrint = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();

    setPrintHtml(buildSolicitudPrintHTML(item));
    setPrintOpen(true);
  };

  const estadoToken = ESTADO_SOLICITUD[item.estado as EstadoSolicitud];
  const prioridadToken =
    PRIORIDAD_SOLICITUD[item.prioridad as PrioridadSolicitud];

  // Areas activas principales (tipo PRINCIPAL)
  const areasPrincipales = item.areas_activas.filter(
    (a) => a.tipo_participacion === "PRINCIPAL",
  );
  const areasAdjuntas = item.areas_activas.filter(
    (a) => a.tipo_participacion === "ADJUNTA",
  );

  const nombreCompleto =
    item.expediente.razon_social ||
    [item.expediente.nombres, item.expediente.apellidos]
      .filter(Boolean)
      .join(" ") ||
    "—";

  const fechaLimite = item.fecha_limite ? new Date(item.fecha_limite) : null;
  const vencida = fechaLimite
    ? fechaLimite < new Date() && item.estado !== "FINALIZADA"
    : false;

  return (
    <>
      <Card className="app-card overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm">
        <CardHeader className="border-b border-border/70 px-4 py-2.5">
          <div className="grid gap-3 md:grid-cols-[auto_1fr_auto] md:items-center">
            <div className="space-y-1">
              <span className="inline-flex rounded-full border border-border bg-background px-3 py-1 font-mono text-[11px] font-black text-foreground">
                {item.expediente.id_publico}
              </span>
              <p className="font-mono text-[10px] font-bold uppercase text-muted-foreground">
                {getTipoDocumentoLabel(item.expediente.tipo_documento)}
              </p>
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p
                  className="truncate text-base font-black uppercase text-foreground"
                  title={nombreCompleto}
                >
                  {nombreCompleto}
                </p>
                <Badge
                  className={prioridadToken.badgeClass}
                  variant="secondary"
                >
                  {prioridadToken.label}
                </Badge>
              </div>
              <p className="mt-1 font-mono text-[10px] font-semibold text-muted-foreground">
                {item.expediente.dni
                  ? `DNI: ${item.expediente.dni}`
                  : item.expediente.ruc
                    ? `RUC: ${item.expediente.ruc}`
                    : item.expediente.cip
                      ? `CIP: ${item.expediente.cip}`
                      : "Sin identificación"}
              </p>
            </div>
            <div className="flex items-start justify-between gap-4 md:justify-end">
              <div className="space-y-1 text-[10px] font-semibold text-muted-foreground md:text-right">
                <p className="flex items-center gap-1.5 md:justify-end">
                  <Mail className="h-3 w-3" />
                  <span className="max-w-56 truncate">
                    {item.expediente.correo || "Sin correo"}
                  </span>
                </p>
                <p className="flex items-center gap-1.5 md:justify-end">
                  <Paperclip className="h-3 w-3" />
                  Folios: {item.expediente.numero_folios}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
                onClick={handlePrint}
                aria-label="Imprimir solicitud"
                title="Imprimir solicitud"
              >
                <Printer className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-2.5 p-4 py-3">
          <div className="rounded-lg border border-border/80 bg-background px-3 py-2.5">
            <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
              Asunto expediente
            </p>
            <p className="mt-1 line-clamp-2 text-xs font-black uppercase text-foreground">
              {item.expediente.asunto}
            </p>
          </div>

          <div className="rounded-lg border border-border/80 bg-background px-3 py-2.5">
            <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
              Documentos expediente
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span>Archivo:</span>
              <span className="inline-flex items-center gap-1 rounded-md border border-primary/20 bg-primary/5 px-2 py-1 text-[10px] font-black text-primary">
                <Paperclip className="h-3 w-3" />
                Principal
              </span>
              <span className="text-muted-foreground">
                Folios: {item.expediente.numero_folios}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-border/70 pt-2.5 text-xs font-bold text-muted-foreground">
            <Calendar className="h-3.5 w-3.5 text-primary" />
            Creado:
            <span className="font-mono text-foreground">
              {new Date(item.fecha_registro).toLocaleString("es-PE", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>

          <div className="rounded-lg border border-primary/25 bg-primary/[0.035] px-3 py-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <Briefcase className="h-4 w-4 text-primary" />
              <span className="text-[10px] font-black uppercase tracking-wide text-primary">
                Solicitud en proceso
              </span>
              <Badge className={estadoToken.badgeClass} variant="secondary">
                {estadoToken.label}
              </Badge>
            </div>

            <div className="mt-2.5 rounded-lg border border-border/70 bg-background px-3 py-2.5">
              <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
                Área principal
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {areasPrincipales.length > 0 ? (
                  areasPrincipales.map((area) => (
                    <span
                      key={area.area_id}
                      className="rounded-md border border-primary/20 bg-primary/5 px-2 py-1 text-xs font-bold text-primary"
                    >
                      {area.area_nombre}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-muted-foreground">
                    Sin área principal
                  </span>
                )}
              </div>
              {areasAdjuntas.length > 0 && (
                <>
                  <p className="mt-2 text-[10px] font-black uppercase tracking-wide text-muted-foreground">
                    Áreas adjuntas
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {areasAdjuntas.map((area) => (
                      <span
                        key={area.area_id}
                        className="rounded-md border border-border bg-muted/40 px-2 py-1 text-xs font-semibold text-muted-foreground"
                      >
                        {area.area_nombre}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="mt-2.5 grid gap-2 md:grid-cols-2">
              <div className="rounded-lg border border-border/70 bg-background px-3 py-2.5">
                <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
                  Inicio solicitud
                </p>
                <p className="mt-1 font-mono text-xs font-black text-foreground">
                  {item.fecha_inicio_gestion
                    ? new Date(item.fecha_inicio_gestion).toLocaleString(
                        "es-PE",
                        {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        },
                      )
                    : "Sin inicio"}
                </p>
              </div>
              <div
                className={cn(
                  "rounded-lg border bg-background px-3 py-2.5",
                  vencida
                    ? "border-destructive/35 bg-destructive/5"
                    : "border-border/70",
                )}
              >
                <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
                  Límite solicitud
                </p>
                <p
                  className={cn(
                    "mt-1 font-mono text-xs font-black",
                    vencida ? "text-destructive" : "text-foreground",
                  )}
                >
                  {fechaLimite
                    ? fechaLimite.toLocaleString("es-PE", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "Sin fecha límite"}
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border/70 pt-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <Dialog open={obsOpen} onOpenChange={setObsOpen}>
                <DialogContent
                  onInteractOutside={(e) => e.preventDefault()}
                  onEscapeKeyDown={(e) => e.preventDefault()}
                  className="max-w-sm"
                >
                  <DialogHeader>
                    <DialogTitle>Observaciones</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-3 text-sm">
                    {item.expediente.observaciones ? (
                      <p className="whitespace-pre-wrap text-muted-foreground">
                        {item.expediente.observaciones}
                      </p>
                    ) : (
                      <p className="text-muted-foreground italic">
                        Sin observaciones registradas
                      </p>
                    )}
                    <div className="pt-2 border-t text-xs text-muted-foreground space-y-1">
                      <p>
                        <span className="font-semibold">Solicitud:</span>{" "}
                        {item.expediente.id_publico}
                      </p>
                      <p>
                        <span className="font-semibold">Estado:</span>{" "}
                        {ESTADO_SOLICITUD[item.estado as EstadoSolicitud].label}
                      </p>
                      <p>
                        <span className="font-semibold">Prioridad:</span>{" "}
                        {
                          PRIORIDAD_SOLICITUD[
                            item.prioridad as PrioridadSolicitud
                          ].label
                        }
                      </p>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                onClick={(e) => {
                  e.stopPropagation();
                  setObsOpen(true);
                }}
                title="Ver observaciones"
              >
                Obs.
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  router.push(`/solicitudes/${item.id}`);
                }}
              >
                <Eye className="h-3.5 w-3.5 mr-1" />
                Ver solicitud
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <PrintPreviewModal
        open={printOpen}
        onOpenChange={setPrintOpen}
        title={`Solicitud ${item.expediente.id_publico}`}
        htmlContent={printHtml}
        previewContent={<SolicitudPrintPreview item={item} />}
      />
    </>
  );
}

/**
 * Loading skeleton for SolicitudCard — matches card dimensions.
 */
export function SolicitudCardSkeleton() {
  return (
    <Card className="app-card animate-pulse rounded-2xl border-border/80">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-28" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-5 w-16" />
            </div>
          </div>
          <Skeleton className="h-5 w-5" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-4 pt-0">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <div className="grid gap-3 lg:grid-cols-3">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
        </div>
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-16" />
        </div>
      </CardContent>
    </Card>
  );
}
