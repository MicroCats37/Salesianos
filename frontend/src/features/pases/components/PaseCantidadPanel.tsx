"use client";

import { Minus, Plus } from "lucide-react";
import { useFormContext } from "react-hook-form";
import { Button } from "@/components/ui/button";
import type { PaseCatalogo, PaseCompraFormData } from "../schemas";
import { formatearMontoPase, paseTotal } from "../utils/pase.precio";

/**
 * PaseCantidadPanel — the quantity and the total of the batch, BEFORE the
 * purchase exists.
 *
 * It is a SMART FIELD: the state comes from the context of `GenericForm` and
 * the component NEVER owns a value and NEVER validates by itself
 * (`contract/smart.md` §2). The buttons are real buttons with labels, so the
 * quantity can be changed with the keyboard alone.
 */

export interface PaseCantidadPanelProps {
  /** The selected pass — `null` while nothing is selected. */
  pase: PaseCatalogo | null;
  /** The maximum quantity accepted for the selected pass. */
  limite: number;
}

export function PaseCantidadPanel({ pase, limite }: PaseCantidadPanelProps) {
  const {
    register,
    setValue,
    watch,
    formState: { errors },
  } = useFormContext<PaseCompraFormData>();

  const cantidad = watch("cantidad");
  const valor = Number.isFinite(cantidad) ? cantidad : 1;
  const total = pase ? paseTotal(pase, valor) : null;
  const errorCantidad = errors.cantidad?.message;

  return (
    <section
      aria-labelledby="pase-confirmacion-titulo"
      className="rounded-3xl border border-slate-200 bg-slate-50 p-5"
    >
      <h2
        id="pase-confirmacion-titulo"
        className="text-xs font-black uppercase tracking-widest text-slate-500"
      >
        Confirmación del pedido
      </h2>

      {pase ? (
        <>
          <p className="mt-2 text-lg font-black text-slate-900">
            {pase.nombre}
          </p>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="pase-cantidad"
                className="block text-sm font-bold text-slate-700"
              >
                ¿Cuántos pases quieres?
              </label>
              <p
                id="pase-cantidad-ayuda"
                className="text-xs font-medium text-slate-500"
              >
                {`Máximo ${limite} por compra.`}
              </p>
              <div className="mt-2 flex items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  aria-label="Quitar un pase"
                  disabled={valor <= 1}
                  onClick={() =>
                    setValue("cantidad", Math.max(1, valor - 1), {
                      shouldValidate: true,
                    })
                  }
                >
                  <Minus className="size-4" aria-hidden="true" />
                </Button>

                <input
                  id="pase-cantidad"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={limite}
                  step={1}
                  aria-describedby="pase-cantidad-ayuda"
                  aria-invalid={errorCantidad ? true : undefined}
                  className="h-10 w-24 rounded-xl border border-slate-300 bg-white px-3 text-center text-base font-black text-slate-900 focus:border-[#312e8e] focus:outline-none focus:ring-2 focus:ring-[#312e8e]/30"
                  {...register("cantidad", { valueAsNumber: true })}
                />

                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  aria-label="Agregar un pase"
                  disabled={valor >= limite}
                  onClick={() =>
                    setValue("cantidad", Math.min(limite, valor + 1), {
                      shouldValidate: true,
                    })
                  }
                >
                  <Plus className="size-4" aria-hidden="true" />
                </Button>
              </div>
              {errorCantidad ? (
                <p role="alert" className="mt-2 text-xs font-bold text-red-700">
                  {errorCantidad}
                </p>
              ) : null}
            </div>

            <dl className="rounded-2xl border border-slate-200 bg-white p-4 text-sm">
              <div className="flex items-baseline justify-between gap-2">
                <dt className="font-bold text-slate-600">Precio por pase</dt>
                <dd className="font-bold text-slate-900">
                  {formatearMontoPase(pase.precio_vigente)}
                </dd>
              </div>
              <div className="mt-2 flex items-baseline justify-between gap-2">
                <dt className="font-bold text-slate-600">Cantidad</dt>
                <dd className="font-bold text-slate-900">{valor}</dd>
              </div>
              <div className="mt-3 flex items-baseline justify-between gap-2 border-t border-slate-200 pt-3">
                <dt className="text-xs font-black uppercase tracking-wider text-slate-500">
                  Total
                </dt>
                <dd className="text-xl font-black text-[#312e8e]">
                  {formatearMontoPase(total)}
                </dd>
              </div>
            </dl>
          </div>
        </>
      ) : (
        <p className="mt-2 text-sm font-medium text-slate-600">
          Selecciona un pase del catálogo para confirmar la cantidad y el total.
        </p>
      )}
    </section>
  );
}
