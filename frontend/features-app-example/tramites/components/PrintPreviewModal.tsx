/**
 * PrintPreviewModal — reusable modal for print previews of Expediente and Solicitud.
 * Shows an elegant styled preview inside a Dialog, with an Imprimir button that
 * triggers browser print for the modal content only.
 *
 * UX flow: card "Imprimir" → modal opens → user reviews → clicks "Imprimir" → browser prints
 */
"use client";

import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PrintPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  /** HTML string used only for iframe/browser print output. */
  htmlContent: string;
  /** Optional React content rendered as the modal body preview. When provided, replaces dangerouslySetInnerHTML. */
  previewContent?: React.ReactNode;
}

export function PrintPreviewModal({
  open,
  onOpenChange,
  title,
  htmlContent,
  previewContent,
}: PrintPreviewModalProps) {
  const handlePrint = () => {
    if (!htmlContent) return;

    // Create an iframe for precise modal-only printing
    const iframe = document.createElement("iframe");
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "0";
    iframe.setAttribute("aria-hidden", "true");
    document.body.appendChild(iframe);

    const iframeDoc = iframe.contentWindow?.document;
    if (!iframeDoc) {
      document.body.removeChild(iframe);
      return;
    }

    const styles = `
      <style>
        @page { margin: 18mm; }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          color: #1b1b1f;
          font-family: Inter, "Plus Jakarta Sans", Arial, sans-serif;
          background: #fff;
        }
        .sheet {
          min-height: 100vh;
          padding: 32px;
          border: 1px solid #ead8d9;
          border-radius: 28px;
          background:
            radial-gradient(circle at top right, rgba(197, 145, 54, .16), transparent 260px),
            linear-gradient(135deg, rgba(130, 15, 31, .08), rgba(255, 255, 255, .96) 42%);
        }
        .brand {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 24px;
          padding-bottom: 22px;
          border-bottom: 2px solid #8f1027;
        }
        .brand-title { font-size: 12px; font-weight: 900; letter-spacing: .18em; color: #8f1027; text-transform: uppercase; }
        .brand-subtitle { margin-top: 4px; font-size: 11px; color: #6b5b60; text-transform: uppercase; letter-spacing: .12em; }
        .seal {
          height: 54px;
          width: 54px;
          border-radius: 999px;
          background: #8f1027;
          color: #fff;
          display: grid;
          place-items: center;
          font-weight: 900;
          letter-spacing: .08em;
        }
        h1 { margin: 30px 0 6px; font-size: 34px; line-height: 1; letter-spacing: -.04em; }
        .public-id { color: #8f1027; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 900; }
        .summary { margin: 18px 0 28px; max-width: 720px; color: #4d4650; font-size: 15px; line-height: 1.65; }
        .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
        .field {
          padding: 14px 16px;
          border: 1px solid #ead8d9;
          border-radius: 18px;
          background: rgba(255,255,255,.78);
        }
        .label { color: #8f1027; font-size: 10px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; }
        .value { margin-top: 6px; font-size: 14px; font-weight: 700; color: #211b20; }
        .full { grid-column: 1 / -1; }
        .badges { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 0; }
        .badge { border: 1px solid #e2c8cb; border-radius: 999px; padding: 6px 10px; color: #8f1027; background: #fff7f5; font-size: 12px; font-weight: 800; }
        .areas-section { margin-top: 18px; }
        .areas-title { font-size: 10px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; color: #8f1027; margin-bottom: 10px; }
        .area-badge { border: 1px solid #e2c8cb; border-radius: 999px; padding: 4px 10px; color: #8f1027; background: #fff7f5; font-size: 12px; font-weight: 700; display: inline-block; margin: 3px; }
        .area-section-badge { display: inline-block; border: 1px solid #e2c8cb; border-radius: 999px; padding: 4px 10px; font-size: 11px; font-weight: 700; }
        .footer { margin-top: 34px; padding-top: 18px; border-top: 1px solid #ead8d9; color: #746a70; font-size: 11px; display: flex; justify-content: space-between; }
        @media print { html, body { margin: 0; padding: 0; } .sheet { border: 0; padding: 16px; border-radius: 0; } }
      </style>
    `;

    iframeDoc.open();
    iframeDoc.write(
      `<!doctype html><html lang="es"><head><meta charset="utf-8" /><title>${title}</title>${styles}</head><body>${htmlContent}</body></html>`,
    );
    iframeDoc.close();

    iframe.contentWindow?.focus();
    iframe.contentWindow?.print();

    // Clean up after printing or cancellation
    const cleanup = () => {
      if (document.body.contains(iframe)) {
        document.body.removeChild(iframe);
      }
    };
    iframe.contentWindow?.addEventListener("afterprint", cleanup, {
      once: true,
    });
    setTimeout(cleanup, 5000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-h-[90vh] flex flex-col p-0 gap-0 sm:!max-w-none"
        style={{
          width: "min(1120px, calc(100vw - 2rem))",
          maxWidth: "min(1120px, calc(100vw - 2rem))",
        }}
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader className="shrink-0 px-5 py-3 border-b border-border flex flex-row items-center justify-between">
          <DialogTitle className="text-lg font-bold">{title}</DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 overflow-hidden bg-muted/20">
          {previewContent ? (
            <div className="p-5">{previewContent}</div>
          ) : (
            <div
              className="[&_.sheet]:!min-h-auto [&_.sheet]:!border [&_.sheet]:!rounded-2xl [&_.sheet]:!shadow-sm"
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
          )}
        </ScrollArea>

        <div className="shrink-0 px-5 py-3 border-t border-border flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cerrar
          </Button>
          <Button variant="default" onClick={handlePrint}>
            <Printer className="size-4" />
            Imprimir
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
