import type { ExpedienteItem, SolicitudItem } from "../schemas/tramite.schema";

// ── Shared helpers ─────────────────────────────────────────────────────────────

function escapeHtml(value: unknown): string {
  return String(value ?? "-")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
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

function personaLabel(exp: ExpedienteItem): string {
  if (exp.razon_social) return exp.razon_social;
  const fullName = [exp.nombres, exp.apellidos].filter(Boolean).join(" ");
  return fullName || "-";
}

function identityLabel(exp: ExpedienteItem): string {
  return exp.dni || exp.ruc || exp.cip || "-";
}

// ── Expediente HTML builder ───────────────────────────────────────────────────

function buildArchivoSummary(archivos: ExpedienteItem["archivos"]): string {
  if (!archivos.length) return '<span class="value">Sin archivos</span>';
  const principal = archivos.filter((a) => a.tipo_archivo === "PRINCIPAL");
  const anexos = archivos.filter((a) => a.tipo_archivo === "ANEXO");
  const parts: string[] = [];
  if (principal.length)
    parts.push(
      `<span class="badge">${principal.length} principal${principal.length !== 1 ? "es" : ""}</span>`,
    );
  if (anexos.length)
    parts.push(
      `<span class="badge">${anexos.length} anexo${anexos.length !== 1 ? "s" : ""}</span>`,
    );
  return parts.join(" ");
}

function buildArchivosField(archivos: ExpedienteItem["archivos"]): string {
  if (!archivos.length) return "";
  return `<div class="field full"><div class="label">Archivos</div><div class="value" style="display:flex;flex-wrap:wrap;gap:6px">${buildArchivoSummary(archivos)}</div></div>`;
}

export function buildExpedientePrintHTML(expediente: ExpedienteItem): string {
  const obs = expediente.observaciones
    ? `<div class="field full"><div class="label">Observaciones</div><div class="value">${escapeHtml(expediente.observaciones)}</div></div>`
    : "";

  return `
    <main class="sheet">
      <section class="brand">
        <div>
          <div class="brand-title">Colegio de Ingenieros del Perú</div>
          <div class="brand-subtitle">Trámite Documentario</div>
        </div>
        <div class="seal">CIP</div>
      </section>

      <h1>Expediente <span class="public-id">${escapeHtml(expediente.id_publico)}</span></h1>
      <p class="summary">${escapeHtml(expediente.asunto)}</p>

      <section class="grid">
        <div class="field"><div class="label">ID Interno</div><div class="value">${escapeHtml(expediente.id)}</div></div>
        <div class="field"><div class="label">N.° Registro</div><div class="value">${escapeHtml(expediente.numero)}</div></div>
        <div class="field"><div class="label">Tipo de persona</div><div class="value">${escapeHtml(expediente.tipo_persona)}</div></div>
        <div class="field"><div class="label">Identificación</div><div class="value" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace">${escapeHtml(identityLabel(expediente))}</div></div>
        <div class="field full"><div class="label">Persona o entidad</div><div class="value">${escapeHtml(personaLabel(expediente))}</div></div>
        <div class="field"><div class="label">Documento</div><div class="value">${escapeHtml(getTipoDocumentoLabel(expediente.tipo_documento))} ${escapeHtml(expediente.numero_documento || "-")}</div></div>
        <div class="field"><div class="label">Folios</div><div class="value">${escapeHtml(expediente.numero_folios)}</div></div>
        <div class="field"><div class="label">Correo</div><div class="value">${escapeHtml(expediente.correo || "-")}</div></div>
        <div class="field"><div class="label">Teléfono</div><div class="value">${escapeHtml(expediente.telefono || "-")}</div></div>
        ${obs}
        ${buildArchivosField(expediente.archivos)}
      </section>

      <div class="badges">
        <span class="badge">Registro: ${escapeHtml(formatDate(expediente.fecha_registro))}</span>
        <span class="badge">Archivos: ${escapeHtml(expediente.archivos.length)}</span>
      </div>

      <footer class="footer">
        <span>Mesa de Partes - Colegio de Ingenieros del Perú</span>
        <span>Impreso desde el sistema</span>
      </footer>
    </main>
  `;
}

// ── Solicitud HTML builder ───────────────────────────────────────────────────

export function buildSolicitudPrintHTML(solicitud: SolicitudItem): string {
  const exp = solicitud.expediente;
  const estadoToken = solicitud.estado;
  const prioridadToken = solicitud.prioridad;

  const areasPrincipales = solicitud.areas_activas.filter(
    (a) => a.tipo_participacion === "PRINCIPAL",
  );
  const areasAdjuntas = solicitud.areas_activas.filter(
    (a) => a.tipo_participacion === "ADJUNTA",
  );
  const allAreas = [...areasPrincipales, ...areasAdjuntas];

  const areasHTML = allAreas.length
    ? `<div class="areas-section">
        <div class="areas-title">Derivado a</div>
        ${allAreas
          .map((a) => {
            const tipo =
              a.tipo_participacion === "PRINCIPAL"
                ? `<span class="area-badge">${escapeHtml(a.area_nombre)}</span>`
                : `<span class="area-section-badge" style="color:#746a70;border-color:#d4c0c4">${escapeHtml(a.area_nombre)} (Adjunta)</span>`;
            return tipo;
          })
          .join("")}
       </div>`
    : `<div class="areas-section"><div class="areas-title">Derivado a</div><span class="value">Sin derivación</span></div>`;

  const obs = exp.observaciones
    ? `<div class="field full"><div class="label">Observaciones</div><div class="value">${escapeHtml(exp.observaciones)}</div></div>`
    : "";

  return `
    <main class="sheet">
      <section class="brand">
        <div>
          <div class="brand-title">Colegio de Ingenieros del Perú</div>
          <div class="brand-subtitle">Trámite Documentario</div>
        </div>
        <div class="seal">CIP</div>
      </section>

      <h1>Solicitud <span class="public-id">${escapeHtml(exp.id_publico)}</span></h1>
      <p class="summary">${escapeHtml(exp.asunto)}</p>

      <section class="grid">
        <div class="field"><div class="label">ID Solicitud</div><div class="value" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px">${escapeHtml(solicitud.id)}</div></div>
        <div class="field"><div class="label">Expediente N.°</div><div class="value">${escapeHtml(exp.numero)}</div></div>
        <div class="field"><div class="label">Estado</div><div class="value">${escapeHtml(estadoToken)}</div></div>
        <div class="field"><div class="label">Prioridad</div><div class="value">${escapeHtml(prioridadToken)}</div></div>
        <div class="field"><div class="label">ID Interno Expediente</div><div class="value" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px">${escapeHtml(exp.id)}</div></div>
        <div class="field"><div class="label">Tipo de persona</div><div class="value">${escapeHtml(exp.tipo_persona)}</div></div>
        <div class="field"><div class="label">Identificación</div><div class="value" style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace">${escapeHtml(identityLabel(exp))}</div></div>
        <div class="field full"><div class="label">Persona o entidad</div><div class="value">${escapeHtml(personaLabel(exp))}</div></div>
        <div class="field"><div class="label">Documento</div><div class="value">${escapeHtml(getTipoDocumentoLabel(exp.tipo_documento))} ${escapeHtml(exp.numero_documento || "-")}</div></div>
        <div class="field"><div class="label">Folios</div><div class="value">${escapeHtml(exp.numero_folios)}</div></div>
        <div class="field"><div class="label">Correo</div><div class="value">${escapeHtml(exp.correo || "-")}</div></div>
        <div class="field"><div class="label">Teléfono</div><div class="value">${escapeHtml(exp.telefono || "-")}</div></div>
        ${obs}
      </section>

      ${areasHTML}

      <div class="badges">
        <span class="badge">Registro: ${escapeHtml(formatDate(solicitud.fecha_registro))}</span>
        ${
          solicitud.fecha_inicio_gestion
            ? `<span class="badge">Inicio gestión: ${escapeHtml(formatDate(solicitud.fecha_inicio_gestion))}</span>`
            : ""
        }
        ${
          solicitud.fecha_limite
            ? `<span class="badge">Fecha límite: ${escapeHtml(formatDate(solicitud.fecha_limite))}</span>`
            : ""
        }
        <span class="badge">Pendiente: ${escapeHtml(solicitud.conteo_pendiente)}</span>
        <span class="badge">En gestión: ${escapeHtml(solicitud.conteo_en_gestion)}</span>
        <span class="badge">Archivos: ${escapeHtml(exp.archivos.length)}</span>
      </div>

      <footer class="footer">
        <span>Mesa de Partes - Colegio de Ingenieros del Perú</span>
        <span>Impreso desde el sistema</span>
      </footer>
    </main>
  `;
}

// ── Legacy print window helper (used during transition) ──────────────────────

/**
 * Opens a print window with the given HTML content.
 * Still used by components that need immediate window.open+print (e.g. detail pages).
 */
export function printWithWindow(htmlContent: string, title: string) {
  const printable = window.open("", "_blank", "width=960,height=720");
  if (!printable) return;
  printable.document.write(`
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <title>${escapeHtml(title)}</title>
        <style>
          @page { margin: 18mm; }
          * { box-sizing: border-box; }
          body { margin: 0; color: #1b1b1f; font-family: Inter, "Plus Jakarta Sans", Arial, sans-serif; background: #fff; }
          .sheet { min-height: 100vh; padding: 32px; border: 1px solid #ead8d9; border-radius: 28px; background: radial-gradient(circle at top right, rgba(197, 145, 54, .16), transparent 260px), linear-gradient(135deg, rgba(130, 15, 31, .08), rgba(255, 255, 255, .96) 42%); }
          .brand { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding-bottom: 22px; border-bottom: 2px solid #8f1027; }
          .brand-title { font-size: 12px; font-weight: 900; letter-spacing: .18em; color: #8f1027; text-transform: uppercase; }
          .brand-subtitle { margin-top: 4px; font-size: 11px; color: #6b5b60; text-transform: uppercase; letter-spacing: .12em; }
          .seal { height: 54px; width: 54px; border-radius: 999px; background: #8f1027; color: #fff; display: grid; place-items: center; font-weight: 900; letter-spacing: .08em; }
          h1 { margin: 30px 0 6px; font-size: 34px; line-height: 1; letter-spacing: -.04em; }
          .public-id { color: #8f1027; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 900; }
          .summary { margin: 18px 0 28px; max-width: 720px; color: #4d4650; font-size: 15px; line-height: 1.65; }
          .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
          .field { padding: 14px 16px; border: 1px solid #ead8d9; border-radius: 18px; background: rgba(255,255,255,.78); }
          .label { color: #8f1027; font-size: 10px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; }
          .value { margin-top: 6px; font-size: 14px; font-weight: 700; color: #211b20; }
          .full { grid-column: 1 / -1; }
          .badges { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 0; }
          .badge { border: 1px solid #e2c8cb; border-radius: 999px; padding: 6px 10px; color: #8f1027; background: #fff7f5; font-size: 12px; font-weight: 800; }
          .areas-section { margin-top: 18px; }
          .areas-title { font-size: 10px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; color: #8f1027; margin-bottom: 10px; }
          .area-badge { border: 1px solid #e2c8cb; border-radius: 999px; padding: 4px 10px; color: #8f1027; background: #fff7f5; font-size: 12px; font-weight: 700; display: inline-block; margin: 3px; }
          .area-section-badge { display: inline-block; border: 1px solid #e2c8cb; border-radius: 999px; padding: 4px 10px; font-size: 11px; font-weight: 700; color: #746a70; }
          .footer { margin-top: 34px; padding-top: 18px; border-top: 1px solid #ead8d9; color: #746a70; font-size: 11px; display: flex; justify-content: space-between; }
          @media print { .sheet { border: 0; padding: 0; } }
        </style>
      </head>
      <body>${htmlContent}</body>
    </html>
  `);
  printable.document.close();
  printable.focus();
  printable.print();
}
