/**
 * SolicitudPrintPreview — two-column administrative detail card.
 * Rendered inside PrintPreviewModal. Preserves estado/prioridad context
 * from the nested expediente. Styled to match the legacy modal look:
 * white bordered cards, subtle header bars, wine/primary accents.
 */
"use client";

import {
  Briefcase,
  Calendar,
  FileText,
  MapPin,
  Timer,
  User,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  ESTADO_SOLICITUD,
  type EstadoSolicitud,
  PRIORIDAD_SOLICITUD,
  type PrioridadSolicitud,
  TIPO_PERSONA,
  type TipoPersona,
} from "@/shared/constants/tramite.tokens";
import type { SolicitudItem } from "../schemas/tramite.schema";

interface SolicitudPrintPreviewProps {
  item: SolicitudItem;
}

function SectionCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon?: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border/80 bg-white shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-muted/40 border-b border-border/60">
        {Icon && <Icon className="h-3.5 w-3.5 text-primary shrink-0" />}
        <span className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">
          {title}
        </span>
      </div>
      <div className="p-3 space-y-2">{children}</div>
    </div>
  );
}

/** Safe accessor for tipo_documento which may be a string or {id,nombre,descripcion} object. */
function getTipoDocumentoLabel(td: unknown): string {
  if (!td) return "—";
  if (typeof td === "object" && "nombre" in (td as object)) {
    return (td as { nombre: string }).nombre;
  }
  if (typeof td === "string") return td;
  return "—";
}

function FieldRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string | number | null | undefined;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-[10px] font-semibold text-muted-foreground shrink-0">
        {label}
      </span>
      <span
        className={`text-xs font-bold text-foreground text-right ${mono ? "font-mono" : ""}`}
        style={{ wordBreak: "break-word" }}
      >
        {value ?? "—"}
      </span>
    </div>
  );
}

export function SolicitudPrintPreview({ item }: SolicitudPrintPreviewProps) {
  const estadoToken = ESTADO_SOLICITUD[item.estado as EstadoSolicitud];
  const prioridadToken =
    PRIORIDAD_SOLICITUD[item.prioridad as PrioridadSolicitud];
  const exp = item.expediente;
  const tipoPersonaToken = TIPO_PERSONA[exp.tipo_persona as TipoPersona];

  const nombreCompleto =
    exp.razon_social ||
    [exp.nombres, exp.apellidos].filter(Boolean).join(" ") ||
    "—";

  const documentoIdentidad = exp.dni || exp.ruc || exp.cip || "—";

  const areasPrincipales = item.areas_activas.filter(
    (a) => a.tipo_participacion === "PRINCIPAL",
  );
  const areasAdjuntas = item.areas_activas.filter(
    (a) => a.tipo_participacion === "ADJUNTA",
  );

  const fechaLimite = item.fecha_limite ? new Date(item.fecha_limite) : null;
  const vencida = fechaLimite
    ? fechaLimite < new Date() && item.estado !== "FINALIZADA"
    : false;

  return (
    <div className="space-y-4">
      {/* ── Modal header: icon left, big ID/title, doc type badge, registration line; right: persona/estado badges ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-white">
            <FileText className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-lg font-black tracking-tight text-primary">
                {exp.id_publico}
              </span>
              <Badge variant="outline" className="text-[10px] font-bold">
                {getTipoDocumentoLabel(exp.tipo_documento)}
              </Badge>
            </div>
            <p className="mt-0.5 text-xs font-semibold text-foreground line-clamp-1">
              {exp.asunto}
            </p>
            <p className="mt-0.5 flex items-center gap-1 text-[10px] text-muted-foreground">
              <Calendar className="h-3 w-3" />
              Registro:{" "}
              {new Date(item.fecha_registro).toLocaleDateString("es-PE", {
                day: "2-digit",
                month: "short",
                year: "numeric",
              })}
            </p>
          </div>
        </div>

        {/* Right-side badges */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <Badge className={tipoPersonaToken.badgeClass} variant="secondary">
            {tipoPersonaToken.label}
          </Badge>
          <Badge className={estadoToken.badgeClass} variant="secondary">
            {estadoToken.label}
          </Badge>
          <Badge className={prioridadToken.badgeClass} variant="secondary">
            {prioridadToken.label}
          </Badge>
        </div>
      </div>

      {/* ── Two-column body ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        {/* LEFT column */}
        <div className="space-y-4">
          {/* Solicitante */}
          <SectionCard title="Solicitante" icon={User}>
            <FieldRow label="Nombre" value={nombreCompleto} />
            <FieldRow label="Documento" value={documentoIdentidad} mono />
            <FieldRow label="Tipo" value={exp.tipo_persona} />
            {exp.telefono && <FieldRow label="Teléfono" value={exp.telefono} />}
            {exp.correo && <FieldRow label="Correo" value={exp.correo} />}
          </SectionCard>

          {/* Expediente */}
          <SectionCard title="Expediente" icon={FileText}>
            <FieldRow label="N.° Registro" value={exp.numero} mono />
            <FieldRow
              label="Documento"
              value={`${getTipoDocumentoLabel(exp.tipo_documento)} ${exp.numero_documento || "—"}`}
              mono
            />
            <FieldRow label="Folios" value={exp.numero_folios} />
            <FieldRow
              label="Archivos"
              value={`${exp.archivos.length} archivo${exp.archivos.length !== 1 ? "s" : ""}`}
            />
            {exp.observaciones && (
              <div className="pt-1 border-t border-border/60">
                <p className="text-[10px] font-semibold text-muted-foreground mb-0.5">
                  Observaciones
                </p>
                <p className="text-xs text-foreground whitespace-pre-wrap">
                  {exp.observaciones}
                </p>
              </div>
            )}
          </SectionCard>

          {/* Adjuntos */}
          <SectionCard title="Adjuntos" icon={MapPin}>
            {areasPrincipales.length > 0 && (
              <div>
                <p className="text-[9px] font-black uppercase tracking-wide text-primary mb-1">
                  Área principal
                </p>
                <div className="flex flex-wrap gap-1">
                  {areasPrincipales.map((area) => (
                    <span
                      key={area.area_id}
                      className="rounded-md border border-primary/20 bg-primary/5 px-2 py-0.5 text-[10px] font-semibold text-primary"
                    >
                      {area.area_nombre}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {areasAdjuntas.length > 0 && (
              <div
                className={
                  areasPrincipales.length > 0
                    ? "pt-2 border-t border-border/60"
                    : ""
                }
              >
                <p className="text-[9px] font-black uppercase tracking-wide text-muted-foreground mb-1">
                  Áreas adjuntas
                </p>
                <div className="flex flex-wrap gap-1">
                  {areasAdjuntas.map((area) => (
                    <span
                      key={area.area_id}
                      className="rounded-md border border-border bg-muted/40 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground"
                    >
                      {area.area_nombre}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {item.areas_activas.length === 0 && (
              <span className="text-xs text-muted-foreground italic">
                Sin derivación
              </span>
            )}
          </SectionCard>
        </div>

        {/* RIGHT column — Gestión del trámite */}
        <div className="space-y-4">
          <SectionCard title="Gestión del trámite" icon={Briefcase}>
            <FieldRow label="Estado" value={estadoToken.label} />
            <FieldRow
              label="Fecha inicio"
              value={
                item.fecha_inicio_gestion
                  ? new Date(item.fecha_inicio_gestion).toLocaleDateString(
                      "es-PE",
                      {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      },
                    )
                  : "—"
              }
            />
            <div className="flex items-start justify-between gap-2">
              <span className="text-[10px] font-semibold text-muted-foreground shrink-0">
                Fecha límite
              </span>
              <span
                className={`text-xs font-bold ${vencida ? "text-destructive" : "text-foreground"}`}
              >
                {fechaLimite
                  ? fechaLimite.toLocaleDateString("es-PE", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })
                  : "—"}
              </span>
            </div>
          </SectionCard>

          {/* Counters */}
          {(item.conteo_pendiente > 0 || item.conteo_en_gestion > 0) && (
            <div className="flex flex-wrap gap-2">
              {item.conteo_pendiente > 0 && (
                <span className="rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-800">
                  {item.conteo_pendiente} pendiente
                  {item.conteo_pendiente !== 1 ? "s" : ""}
                </span>
              )}
              {item.conteo_en_gestion > 0 && (
                <span className="rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-bold text-red-700">
                  {item.conteo_en_gestion} en gestión
                </span>
              )}
            </div>
          )}

          {/* Áreas — PRINCIPAL vs ADJUNTA distinctly */}
          {(areasPrincipales.length > 0 || areasAdjuntas.length > 0) && (
            <SectionCard title="Equipo / Áreas" icon={MapPin}>
              {areasPrincipales.length > 0 && (
                <div className="mb-2">
                  <p className="text-[9px] font-black uppercase tracking-wide text-primary mb-1">
                    Principal
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {areasPrincipales.map((area) => (
                      <span
                        key={area.area_id}
                        className="rounded-md border border-primary/20 bg-primary/5 px-2 py-1 text-xs font-semibold text-primary"
                      >
                        {area.area_nombre}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {areasAdjuntas.length > 0 && (
                <div>
                  <p className="text-[9px] font-black uppercase tracking-wide text-muted-foreground mb-1">
                    Adjunta{areasPrincipales.length > 0 ? "s" : ""}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {areasAdjuntas.map((area) => (
                      <span
                        key={area.area_id}
                        className="rounded-md border border-border bg-muted/40 px-2 py-1 text-xs font-semibold text-muted-foreground"
                      >
                        {area.area_nombre}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </SectionCard>
          )}
        </div>
      </div>
    </div>
  );
}
