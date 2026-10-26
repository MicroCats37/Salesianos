"use client";

import { SlidersHorizontal, X } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export interface AdminFiltrosSheetProps {
  /** Number of active resource filters (the badge of the trigger). */
  activeCount: number;
  /** The "Limpiar filtros" action. */
  onClear: () => void;
  /** The resource filters of the section. */
  children: ReactNode;
}

/**
 * AdminFiltrosSheet — the resource filters of a list on a phone.
 *
 * The filters are NOT rendered inline below 768px: they live inside this
 * sheet, so they are not even in the DOM until the administrator opens them.
 * That is why the branch is decided in JAVASCRIPT and not with a CSS class:
 * a hidden-but-mounted control is still a control.
 *
 * The sheet opens from the bottom (it is within reach of the thumb) and the
 * badge of the trigger says how many filters are narrowing the list.
 */
export function AdminFiltrosSheet({
  activeCount,
  onClear,
  children,
}: AdminFiltrosSheetProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          type="button"
          variant="outline"
          aria-label="Abrir filtros"
          className="h-9 gap-2 rounded-xl px-3 text-xs font-black uppercase tracking-wider"
        >
          <SlidersHorizontal className="size-3.5" />
          Filtros
          {activeCount > 0 ? (
            <span className="rounded-full bg-[#312e8e] px-1.5 text-[10px] font-black text-white">
              {activeCount}
            </span>
          ) : null}
        </Button>
      </SheetTrigger>

      <SheetContent
        side="bottom"
        showCloseButton={false}
        className="max-h-[85vh] overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle className="text-base font-black tracking-tight text-[#17214b]">
            Filtros
          </SheetTitle>
          <SheetDescription className="text-xs text-slate-500">
            Elige los filtros que quieres aplicar a la lista.
          </SheetDescription>
          <SheetClose asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Cerrar filtros"
              className="absolute top-3 right-3"
            >
              <X className="size-4" />
            </Button>
          </SheetClose>
        </SheetHeader>

        <div className="grid gap-3 px-4 sm:grid-cols-2">{children}</div>

        <SheetFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClear}
            className="h-10 w-full rounded-xl text-xs font-black uppercase tracking-wider"
          >
            Limpiar filtros
          </Button>
          <SheetClose asChild>
            <Button
              type="button"
              className="h-10 w-full rounded-xl text-xs font-black uppercase tracking-wider"
            >
              Ver resultados
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
