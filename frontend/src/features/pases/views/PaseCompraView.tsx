"use client";

import { Loader2 } from "lucide-react";
import { useId, useState } from "react";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { IzipayModal } from "@/features/pagos";
import { PaseBeneficiariosPanel } from "../components/PaseBeneficiariosPanel";
import { PaseCantidadPanel } from "../components/PaseCantidadPanel";
import { PaseCatalogoCard } from "../components/PaseCatalogoCard";
import { PaseCompraResultado } from "../components/PaseCompraResultado";
import {
  construirPayloadCompraPase,
  useCrearCompraPase,
} from "../hooks/useCompraPase";
import { useCompraPaseEstado } from "../hooks/useCompraPaseEstado";
import { usePasesCatalogo } from "../hooks/usePasesCatalogo";
import {
  type PaseCatalogo,
  type PaseCompraCreada,
  type PaseCompraFormData,
  paseCompraFormSchema,
} from "../schemas";
import { paseCompraPagable, paseCompraPagada } from "../utils/pase.estado";
import {
  PASE_CANTIDAD_MAXIMA_POR_COMPRA,
  paseCantidadLimite,
} from "../utils/pase.precio";

/**
 * PaseCompraView — the purchase of the party passes.
 *
 * The flow is DEDICATED to the passes: it is NOT a branch of the sports
 * wizard. It goes from the catalogue to the confirmation of the amount, then
 * it registers the purchase and hands it to the SHARED payment modal
 * (`features/pagos`), which is the only component that talks to the payment
 * provider.
 *
 * The state of the purchase is read from the backend AFTER the payment
 * (`useCompraPaseEstado`): the browser never decides that an activation
 * completed.
 */
export function PaseCompraView() {
  const formId = useId();
  const [compraId, setCompraId] = useState<string | null>(null);
  const [compraCreada, setCompraCreada] = useState<PaseCompraCreada | null>(
    null,
  );
  const [modalPagoAbierto, setModalPagoAbierto] = useState(false);

  const catalogo = usePasesCatalogo();
  const crear = useCrearCompraPase();
  const { data: compra, refetch: refetchCompra } =
    useCompraPaseEstado(compraId);

  const visible = compra ?? compraCreada;
  const pagable = visible
    ? paseCompraPagable({
        estado_compra: visible.estado_compra,
        estado_orden: visible.estado_orden,
      })
    : false;

  /** Start another purchase: the previous one is only READ afterwards. */
  function reiniciar() {
    setCompraId(null);
    setCompraCreada(null);
    setModalPagoAbierto(false);
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6">
        <h1 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
          Comprar pase de fiesta
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
          El pase da acceso nominativo a la fiesta, sin inscripción deportiva.
          Elige el pase, confirma la cantidad y completa el pago: el precio lo
          fija el servidor.
        </p>
      </header>

      {catalogo.isLoading ? (
        <output
          aria-label="Cargando el catálogo de pases"
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        >
          {[0, 1, 2].map((indice) => (
            <Skeleton key={indice} className="h-56 w-full rounded-3xl" />
          ))}
        </output>
      ) : null}

      {catalogo.isError ? (
        <p
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-bold text-red-800"
        >
          {catalogo.error?.message ??
            "No se pudo cargar el catálogo de pases de fiesta."}
        </p>
      ) : null}

      {catalogo.data?.length === 0 ? (
        <p className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-medium text-slate-600">
          Los pases de fiesta todavía no están disponibles.
        </p>
      ) : null}

      {visible ? (
        <div className="mb-6 space-y-4">
          <PaseCompraResultado
            numeroOrden={visible.numero_orden}
            paseNombre={visible.pase_nombre}
            cantidad={visible.cantidad}
            precioUnitario={visible.precio_unitario}
            total={visible.total}
            moneda={compra?.moneda ?? null}
            estado={{
              estado_compra: visible.estado_compra,
              estado_orden: visible.estado_orden,
            }}
            origenPago={compra?.origen_pago ?? null}
            beneficiariosAsignados={compra?.beneficiarios_asignados ?? null}
            beneficiariosPendientes={compra?.beneficiarios_pendientes ?? null}
            pagable={pagable}
            onPagar={() => setModalPagoAbierto(true)}
          />

          <Button
            type="button"
            variant="outline"
            onClick={reiniciar}
            className="w-full rounded-full font-black sm:w-auto"
          >
            Comprar otro pase
          </Button>
        </div>
      ) : null}

      {visible && compraId && paseCompraPagada(visible) ? (
        <div className="mt-6">
          <PaseBeneficiariosPanel compraId={compraId} />
        </div>
      ) : null}

      <GenericForm<PaseCompraFormData>
        formId={formId}
        schema={paseCompraFormSchema}
        initialData={{ pase_id: "", cantidad: 1 }}
        isLoading={crear.isPending}
        skipFooter
        onSubmit={async (datos) => {
          const payload = construirPayloadCompraPase(datos);
          const compraNueva = await crear.mutateAsync(payload);
          setCompraCreada(compraNueva);
          setCompraId(compraNueva.compra_id);
          setModalPagoAbierto(true);
        }}
      >
        {({ methods, isSubmitting, submissionMessage }) => {
          const paseId = methods.watch("pase_id");
          const seleccionado: PaseCatalogo | null =
            catalogo.data?.find((pase) => pase.id === paseId) ?? null;
          const limite = seleccionado
            ? paseCantidadLimite(seleccionado)
            : PASE_CANTIDAD_MAXIMA_POR_COMPRA;

          return (
            <div className="space-y-4">
              <section aria-labelledby="pase-seleccion-titulo">
                <h2
                  id="pase-seleccion-titulo"
                  className="text-xs font-black uppercase tracking-widest text-slate-500"
                >
                  Elige tu pase
                </h2>
                <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {(catalogo.data ?? []).map((pase) => (
                    <PaseCatalogoCard
                      key={pase.id}
                      pase={pase}
                      seleccionado={pase.id === paseId}
                      deshabilitado={isSubmitting}
                      onSeleccionar={(elegido: PaseCatalogo) => {
                        methods.setValue("pase_id", elegido.id, {
                          shouldValidate: true,
                        });
                        methods.setValue("cantidad", 1, {
                          shouldValidate: true,
                        });
                      }}
                    />
                  ))}
                </div>
              </section>

              {visible ? null : (
                <>
                  <PaseCantidadPanel pase={seleccionado} limite={limite} />

                  {submissionMessage?.type === "error" ? (
                    <p
                      role="alert"
                      className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-800"
                    >
                      {submissionMessage.message}
                    </p>
                  ) : null}

                  <Button
                    type="submit"
                    form={formId}
                    disabled={isSubmitting || !seleccionado}
                    className="btn-brand-gradient w-full rounded-full font-black text-white"
                  >
                    {isSubmitting ? (
                      <Loader2
                        className="mr-2 size-4 animate-spin"
                        aria-hidden="true"
                      />
                    ) : null}
                    {isSubmitting
                      ? "Registrando la compra..."
                      : "Continuar al pago"}
                  </Button>
                </>
              )}
            </div>
          );
        }}
      </GenericForm>

      <IzipayModal
        isOpen={modalPagoAbierto}
        onClose={() => setModalPagoAbierto(false)}
        compraId={compraId}
        onSuccess={async () => {
          await refetchCompra();
        }}
      />
    </main>
  );
}
