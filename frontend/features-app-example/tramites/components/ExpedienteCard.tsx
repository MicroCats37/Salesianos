/**
 * ExpedienteCard — card component for Expediente list display.
 * Shows key expediente fields with token-based badges and clickable navigation.
 */
"use client";

import { Calendar, Eye, Mail, Paperclip, Phone, Printer } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  TIPO_PERSONA,
  type TipoPersona,
} from "@/shared/constants/tramite.tokens";
import type { ExpedienteItem } from "../schemas/tramite.schema";
import { ExpedientePrintPreview } from "./ExpedientePrintPreview";
import { PrintPreviewModal } from "./PrintPreviewModal";
import { buildExpedientePrintHTML } from "./printExpediente";

/** Safe accessor for tipo_documento which may be a string or {id,nombre,descripcion} object. */
function getTipoDocumentoLabel(td: unknown): string {
  if (!td) return "—";
  if (typeof td === "object" && "nombre" in (td as object)) {
    return (td as { nombre: string }).nombre;
  }
  if (typeof td === "string") return td;
  return "—";
}

interface ExpedienteCardProps {
  item: ExpedienteItem;
  onClick?: () => void;
}

export function ExpedienteCard({
  item,
  onClick: _onClick,
}: ExpedienteCardProps) {
  const router = useRouter();

  const [printOpen, setPrintOpen] = useState(false);
  const [printHtml, setPrintHtml] = useState("");

  const handlePrint = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();

    setPrintHtml(buildExpedientePrintHTML(item));
    setPrintOpen(true);
  };

  const tipoToken = TIPO_PERSONA[item.tipo_persona as TipoPersona];

  const nombreCompleto =
    item.razon_social ||
    [item.nombres, item.apellidos].filter(Boolean).join(" ") ||
    "—";

  const documentoIdentidad = item.dni || item.ruc || item.cip || "—";

  return (
    <>
      <Card className="app-card overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm">
        <CardHeader className="border-b border-border/70 px-4 py-2.5">
          <div className="grid gap-3 md:grid-cols-[auto_1fr_auto] md:items-center">
            <div className="space-y-1">
              <span className="inline-flex rounded-full border border-border bg-background px-3 py-1 font-mono text-[11px] font-black text-foreground">
                {item.id_publico}
              </span>
              <p className="font-mono text-[10px] font-bold uppercase text-muted-foreground">
                {getTipoDocumentoLabel(item.tipo_documento)}
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
                <Badge className={tipoToken.badgeClass} variant="secondary">
                  {tipoToken.label}
                </Badge>
              </div>
              <p className="mt-1 font-mono text-[10px] font-semibold text-muted-foreground">
                {item.dni
                  ? `DNI: ${item.dni}`
                  : item.ruc
                    ? `RUC: ${item.ruc}`
                    : item.cip
                      ? `CIP: ${item.cip}`
                      : documentoIdentidad}
              </p>
            </div>
            <div className="flex items-start justify-between gap-4 md:justify-end">
              <div className="space-y-1 text-[10px] font-semibold text-muted-foreground md:text-right">
                <p className="flex items-center gap-1.5 md:justify-end">
                  <Mail className="h-3 w-3" />
                  <span className="max-w-56 truncate">
                    {item.correo || "Sin correo"}
                  </span>
                </p>
                <p className="flex items-center gap-1.5 md:justify-end">
                  <Phone className="h-3 w-3" />
                  {item.telefono || "Sin teléfono"}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
                onClick={handlePrint}
                aria-label="Imprimir expediente"
                title="Imprimir expediente"
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
              {item.asunto}
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
                Folios: {item.numero_folios}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-2.5">
            <span className="inline-flex items-center gap-2 text-xs font-bold text-muted-foreground">
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
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={(e) => {
                e.stopPropagation();
                router.push(`/expedientes/${item.id}`);
              }}
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              Ver expediente
            </Button>
          </div>
        </CardContent>
      </Card>

      <PrintPreviewModal
        open={printOpen}
        onOpenChange={setPrintOpen}
        title={`Expediente ${item.id_publico}`}
        htmlContent={printHtml}
        previewContent={<ExpedientePrintPreview item={item} />}
      />
    </>
  );
}

/**
 * Loading skeleton for ExpedienteCard — matches card dimensions.
 */
export function ExpedienteCardSkeleton() {
  return (
    <Card className="app-card animate-pulse rounded-2xl border-border/80">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-5 w-20" />
          </div>
          <Skeleton className="h-5 w-5" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-4 pt-0">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <div className="grid gap-3 md:grid-cols-3">
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
