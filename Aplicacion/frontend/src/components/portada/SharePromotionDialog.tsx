"use client";

import { ArrowUpRight, Copy, MessageCircle, Share, Share2 } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Promocion } from "@/features/portada/config/promotions";
import { COPY } from "@/features/portada/copy";

export type PromotionDialogMode = "poster" | "compartir";

export interface SharePromotionDialogProps {
  /** Promoción seleccionada. `null` mantiene el diálogo cerrado. */
  promocion: Promocion | null;
  /** `poster` muestra el afiche; `compartir` añade el resumen de la promoción. */
  modo: PromotionDialogMode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Sustituye el marcador `{anio}` del copy editorial. */
function conAnio(texto: string, anio: number) {
  return texto.replace(/\{anio\}/g, String(anio));
}

/**
 * Diálogo de anuncio oficial de una promoción.
 *
 * Reproduce la intención de `openPromotionPoster` / `openPromotionShare` del
 * micrositio: el afiche grande y las cuatro vías de compartir (WhatsApp,
 * Facebook, copiar enlace y el menú nativo del dispositivo).
 */
export function SharePromotionDialog({
  promocion,
  modo,
  open,
  onOpenChange,
}: SharePromotionDialogProps) {
  const [estado, setEstado] = useState("");
  const [mostrarEnlace, setMostrarEnlace] = useState(false);
  const [soportaCompartir, setSoportaCompartir] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setEstado("");
    setMostrarEnlace(false);
    setSoportaCompartir(typeof navigator.share === "function");
  }, [open]);

  useEffect(() => {
    if (!mostrarEnlace) return;
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [mostrarEnlace]);

  if (!promocion) return null;

  const anio = promocion.anio;
  const mensaje = conAnio(COPY.promociones.share.mensaje, anio);
  const enlaceWhatsapp = `https://wa.me/?text=${encodeURIComponent(
    `${mensaje}\n${promocion.fuente}`,
  )}`;
  const enlaceFacebook = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
    promocion.fuente,
  )}`;

  const copiarEnlace = async () => {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard no disponible");
      }
      await navigator.clipboard.writeText(promocion.fuente);
      const aviso = conAnio(COPY.promociones.share.copiado, anio);
      setEstado(aviso);
      toast.success(aviso);
    } catch {
      setMostrarEnlace(true);
      setEstado(COPY.promociones.share.copiarManual);
    }
  };

  const compartirNativo = async () => {
    try {
      await navigator.share({
        title: conAnio(COPY.promociones.share.tituloNativo, anio),
        text: mensaje,
        url: promocion.fuente,
      });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") return;
      setEstado(COPY.promociones.share.errorCompartir);
      toast.error(COPY.promociones.share.errorCompartir);
    }
  };

  const esCompartir = modo === "compartir";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] gap-5 overflow-y-auto sm:max-w-xl">
        <DialogHeader className="pr-8 text-left">
          <p className="text-eyebrow-brand">
            {esCompartir
              ? COPY.promociones.share.eyebrow
              : COPY.promociones.share.posterEyebrow}
          </p>
          <DialogTitle className="text-2xl font-black uppercase leading-[1.05] tracking-tight text-[#17214b] sm:text-3xl">
            {conAnio(
              esCompartir
                ? COPY.promociones.share.titulo
                : COPY.promociones.share.posterTitulo,
              anio,
            )}
          </DialogTitle>
          <DialogDescription className="sr-only">
            {conAnio(COPY.promociones.share.altPoster, anio)}
          </DialogDescription>
        </DialogHeader>

        <div className="mx-auto w-full max-w-[240px] overflow-hidden rounded-2xl bg-[#312e8e]/5">
          <div className="relative aspect-[4/5] w-full">
            <Image
              src={promocion.imagen}
              alt={conAnio(COPY.promociones.share.altPoster, anio)}
              fill
              sizes="240px"
              className="object-cover"
            />
          </div>
        </div>

        {esCompartir && (
          <div className="rounded-2xl border border-[#312e8e]/12 bg-[#f4f6fb] p-5">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#1557b8]">
              {COPY.promociones.share.etiqueta}
            </p>
            <p className="mt-2 text-xl font-black uppercase leading-tight text-[#17214b]">
              {COPY.promociones.share.destacado}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-[#626195]">
              {COPY.promociones.share.fecha} · {COPY.promociones.share.lugar}
            </p>
          </div>
        )}

        <fieldset className="grid gap-3 border-0 p-0 sm:grid-cols-2">
          <legend className="sr-only">
            {conAnio(COPY.promociones.share.compartirAnuncio, anio)}
          </legend>
          <a
            href={enlaceWhatsapp}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#16a34a]/30 bg-[#16a34a]/10 px-4 text-xs font-black uppercase tracking-wider text-[#16a34a] transition-colors hover:bg-[#16a34a]/20"
          >
            <MessageCircle className="size-4" aria-hidden="true" />
            {COPY.promociones.share.whatsapp}
          </a>
          <a
            href={enlaceFacebook}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#1557b8]/30 bg-[#1557b8]/10 px-4 text-xs font-black uppercase tracking-wider text-[#1557b8] transition-colors hover:bg-[#1557b8]/20"
          >
            <Share2 className="size-4" aria-hidden="true" />
            {COPY.promociones.share.facebook}
          </a>
          <button
            type="button"
            onClick={copiarEnlace}
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#312e8e]/25 bg-white px-4 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
          >
            <Copy className="size-4" aria-hidden="true" />
            {COPY.promociones.share.copiar}
          </button>
          {soportaCompartir && (
            <button
              type="button"
              onClick={compartirNativo}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-[#ec4899]/30 bg-[#ec4899]/10 px-4 text-xs font-black uppercase tracking-wider text-[#ec4899] transition-colors hover:bg-[#ec4899]/20"
            >
              <Share className="size-4" aria-hidden="true" />
              {COPY.promociones.share.mas}
            </button>
          )}
        </fieldset>

        {mostrarEnlace && (
          <div className="rounded-xl border border-[#312e8e]/15 bg-[#f4f6fb] p-4">
            <label
              htmlFor="promotion-share-url"
              className="text-[10px] font-black uppercase tracking-[0.2em] text-[#626195]"
            >
              {COPY.promociones.share.etiquetaEnlace}
            </label>
            <input
              id="promotion-share-url"
              ref={inputRef}
              readOnly
              value={promocion.fuente}
              onFocus={(event) => event.currentTarget.select()}
              className="mt-2 h-11 w-full rounded-lg border border-[#312e8e]/20 bg-white px-3 text-sm text-[#17214b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#312e8e]"
            />
            <p className="mt-2 text-xs text-[#626195]">
              {COPY.promociones.share.ayudaEnlace}
            </p>
          </div>
        )}

        <output className="block min-h-5 text-xs font-semibold text-[#1557b8]">
          {estado}
        </output>

        {esCompartir && (
          <p className="text-xs leading-relaxed text-[#626195]">
            {COPY.promociones.share.explicacion}
          </p>
        )}

        <a
          href={promocion.fuente}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-[#312e8e]/25 px-5 text-xs font-black uppercase tracking-wider text-[#312e8e] transition-colors hover:bg-[#312e8e]/5"
        >
          {COPY.promociones.share.verOriginal}
          <ArrowUpRight className="size-4" aria-hidden="true" />
        </a>
      </DialogContent>
    </Dialog>
  );
}
