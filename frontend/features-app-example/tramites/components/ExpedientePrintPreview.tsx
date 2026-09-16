/**
 * ExpedientePrintPreview — two-column administrative detail card for Expediente.
 * Rendered inside PrintPreviewModal. Styled to match the legacy modal look:
 * white bordered cards, subtle header bars, wine/primary accents.
 * Does not fake solicitud gestión data when no solicitud is present.
 */
"use client";

import {
  Building2,
  Calendar,
  FileText,
  Mail,
  Paperclip,
  Phone,
  User,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  TIPO_PERSONA,
  type TipoPersona,
} from "@/shared/constants/tramite.tokens";
import type { ExpedienteItem } from "../schemas/tramite.schema";

/** Safe accessor for tipo_documento which may be a string or {id,nombre,descripcion} object. */
function getTipoDocumentoLabel(td: unknown): string {
  if (!td) return "—";
  if (typeof td === "object" && "nombre" in (td as object)) {
    return (td as { nombre: string }).nombre;
  }
  if (typeof td === "string") return td;
  return "—";
}

interface ExpedientePrintPreviewProps {
  item: ExpedienteItem;
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

export function ExpedientePrintPreview({ item }: ExpedientePrintPreviewProps) {
  const tipoToken = TIPO_PERSONA[item.tipo_persona as TipoPersona];
  const nombreCompleto =
    item.razon_social ||
    [item.nombres, item.apellidos].filter(Boolean).join(" ") ||
    "—";
  const documentoIdentidad = item.dni || item.ruc || item.cip || "—";

  const principalArchivos = item.archivos.filter(
    (a) => a.tipo_archivo === "PRINCIPAL",
  );
  const anexoArchivos = item.archivos.filter((a) => a.tipo_archivo === "ANEXO");

  return (
    <div className="space-y-4">
      {/* ── Modal header: icon left, big ID/title, doc type badge, registration line; right: persona badge ── */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-white">
            <FileText className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-lg font-black tracking-tight text-primary">
                {item.id_publico}
              </span>
              <Badge variant="outline" className="text-[10px] font-bold">
                {getTipoDocumentoLabel(item.tipo_documento)}
              </Badge>
              <Badge className={tipoToken.badgeClass} variant="secondary">
                {tipoToken.label}
              </Badge>
            </div>
            <p className="mt-0.5 text-xs font-semibold text-foreground line-clamp-1">
              {item.asunto}
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

        {/* Right-side badge */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <Badge className={tipoToken.badgeClass} variant="secondary">
            {tipoToken.label}
          </Badge>
        </div>
      </div>

      {/* ── Two-column body ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        {/* LEFT column */}
        <div className="space-y-4">
          {/* Persona / Entidad */}
          <SectionCard
            title="Persona / Entidad"
            icon={item.tipo_persona === "JURIDICA" ? Building2 : User}
          >
            <FieldRow label="Nombre" value={nombreCompleto} />
            <FieldRow label="Documento" value={documentoIdentidad} mono />
            <FieldRow label="Tipo" value={item.tipo_persona} />
            {item.telefono && (
              <FieldRow label="Teléfono" value={item.telefono} />
            )}
            {item.correo && <FieldRow label="Correo" value={item.correo} />}
          </SectionCard>

          {/* Documento */}
          <SectionCard title="Documento" icon={FileText}>
            <FieldRow
              label="Tipo"
              value={getTipoDocumentoLabel(item.tipo_documento)}
            />
            <FieldRow
              label="Número"
              value={item.numero_documento || "—"}
              mono
            />
            <FieldRow label="Folios" value={item.numero_folios} />
          </SectionCard>

          {/* Observaciones */}
          {item.observaciones && (
            <SectionCard title="Observaciones">
              <p className="text-xs text-foreground whitespace-pre-wrap">
                {item.observaciones}
              </p>
            </SectionCard>
          )}
        </div>

        {/* RIGHT column */}
        <div className="space-y-4">
          {/* Archivos */}
          <SectionCard title="Archivos" icon={Paperclip}>
            {item.archivos.length === 0 ? (
              <span className="text-xs text-muted-foreground italic">
                Sin archivos
              </span>
            ) : (
              <div className="space-y-2">
                {principalArchivos.length > 0 && (
                  <div>
                    <p className="text-[9px] font-black uppercase tracking-wide text-primary mb-1">
                      Principal
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {principalArchivos.map((archivo) => (
                        <span
                          key={archivo.id}
                          className="rounded-md border border-primary/20 bg-primary/5 px-2 py-0.5 text-[10px] font-semibold text-primary"
                        >
                          {archivo.nombre_original}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {anexoArchivos.length > 0 && (
                  <div
                    className={
                      principalArchivos.length > 0
                        ? "pt-2 border-t border-border/60"
                        : ""
                    }
                  >
                    <p className="text-[9px] font-black uppercase tracking-wide text-muted-foreground mb-1">
                      Anexo{anexoArchivos.length !== 1 ? "s" : ""}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {anexoArchivos.map((archivo) => (
                        <span
                          key={archivo.id}
                          className="rounded-md border border-border bg-muted/40 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground"
                        >
                          {archivo.nombre_original}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </SectionCard>

          {/* Expediente metadata */}
          <SectionCard title="Expediente" icon={FileText}>
            <FieldRow label="ID Interno" value={item.id} mono />
            <FieldRow label="N.° Registro" value={item.numero} mono />
            <FieldRow
              label="Fecha registro"
              value={new Date(item.fecha_registro).toLocaleDateString("es-PE", {
                day: "2-digit",
                month: "short",
                year: "numeric",
              })}
            />
            <FieldRow label="Archivos" value={item.archivos.length} />
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
