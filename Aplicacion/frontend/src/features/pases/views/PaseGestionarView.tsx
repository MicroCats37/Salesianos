import { Lock, UserRound } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { RouteHero } from "@/components/shell/RouteHero";
import {
  ShellErrorState,
  ShellPendingState,
} from "@/components/shell/ShellState";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ContadoresPases } from "../components/ContadoresPases";
import { EstadoPagoPase } from "../components/EstadoPagoPase";
import { FormularioBeneficiario } from "../components/FormularioBeneficiario";
import { ListaBeneficiarios } from "../components/ListaBeneficiarios";
import type {
  CompraPases,
  EnviarAsignacionPase,
  EstadoVistaPases,
  RevocarBeneficiario,
  VeredictoPago,
} from "../types/pase.types";
import { formatearMonto } from "../utils/monto";

export interface PaseGestionarViewProps {
  /** The private token of the link. It IS the credential. */
  token: string;
  /** The state of the purchase. */
  estado?: EstadoVistaPases;
  /** The purchase of the batch, when the link opens it. */
  compra?: CompraPases;
  /** The verdict of the payment, when there already is an order. */
  pago?: VeredictoPago;
  /**
   * The message of the server when the read failed.
   *
   * It is shown VERBATIM: the interface never rewrites the wording the
   * server chose (`contract/api-wrapper-presenter-contract.md` §8).
   */
  mensajeError?: string;
  /** The transport of the assignment of a pass to a person. */
  asignar?: EnviarAsignacionPase;
  /** The transport of the revocation of an entry right. */
  revocar?: RevocarBeneficiario;
  /** The action that resolves a failed read. */
  reintentar?: () => void;
}
/**
 * PASS-02 - the assignment of the beneficiaries of a purchase.
 *
 * The route is reached with a token in the URL: the token IS the credential
 * and its expiry is the business of the server. The page never asks for a
 * session, because the visitor who bought the passes may not have one.
 *
 * **The denial is NEUTRAL** (`QA-U03`): the same message answers an expired
 * link, a link of somebody else and a wrong document. It never reveals
 * whether a purchase exists, so typing a document is not an oracle.
 */
export function PaseGestionarView({
  token,
  estado = "sin-datos",
  compra,
  pago,
  mensajeError,
  asignar,
  revocar,
  reintentar,
}: PaseGestionarViewProps) {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="PASS-02"
        title="Asignar los beneficiarios de tu compra"
        description="Indica quién usa cada pase. El acceso llega con un enlace propio y sólo permite trabajar sobre esa compra: no hay sesión ni datos de otras compras."
        facts={[{ label: "Acceso", value: `${token.slice(0, 8)}...` }]}
      />

      {estado === "sin-permiso" ? (
        <Alert>
          <Lock className="size-4" aria-hidden="true" />
          <AlertTitle>No pudimos abrir esta compra</AlertTitle>
          <AlertDescription>
            El enlace puede haber caducado o no corresponde a esta compra. Si lo
            has perdido, puedes pedir un enlace nuevo para recuperarla.
          </AlertDescription>
        </Alert>
      ) : null}

      {estado === "cargando" ? (
        <ShellPendingState
          title="Comprobando tu enlace"
          description="Estamos verificando el acceso a esta compra."
        />
      ) : null}

      {estado === "error" ? (
        <ShellErrorState
          title="No pudimos comprobar tu enlace"
          description={
            mensajeError ??
            "No pudimos comprobar el enlace en este momento. Vuelve a intentarlo en unos segundos."
          }
          accion={
            reintentar
              ? { label: "Reintentar", onClick: reintentar }
              : undefined
          }
          className="min-h-11"
        />
      ) : null}

      {estado === "sin-datos" ? (
        <RouteEmptyState
          icon={UserRound}
          title="El enlace todavía no se puede comprobar"
          description="La compra, sus pases y sus beneficiarios llegan del servicio de pases con el token de acceso. Esta pantalla se completará con esa fuente; hasta entonces no se inventa ninguna asignación."
        />
      ) : null}
      {estado === "listo" && compra ? (
        <>
          <section
            aria-labelledby="resumen-compra-pases-titulo"
            className="flex flex-col gap-4 rounded-[var(--radius-xl)] border border-border bg-surface-elevated p-5 shadow-[var(--elevation-md)]"
          >
            <h2
              id="resumen-compra-pases-titulo"
              className="text-section-title text-foreground"
            >
              Tu compra
            </h2>
            <dl className="grid gap-4 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <dt className="text-eyebrow-brand text-muted-foreground">
                  Pase
                </dt>
                <dd className="text-base font-bold text-foreground">
                  {compra.pase_nombre}
                </dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-eyebrow-brand text-muted-foreground">
                  Total
                </dt>
                <dd className="text-base font-bold tabular-nums text-foreground">
                  {formatearMonto(compra.total, compra.moneda)}
                </dd>
              </div>
              <div className="flex flex-col gap-1">
                <dt className="text-eyebrow-brand text-muted-foreground">
                  Estado
                </dt>
                <dd className="text-base font-bold text-foreground">
                  {compra.estado_etiqueta}
                </dd>
              </div>
            </dl>
            {pago ? <EstadoPagoPase veredicto={pago} conDescripcion /> : null}
          </section>

          <ContadoresPases compra={compra} />

          <section
            aria-labelledby="asignar-pase-titulo"
            className="flex flex-col gap-3"
          >
            <h2
              id="asignar-pase-titulo"
              className="text-section-title text-foreground"
            >
              Asignar una entrada
            </h2>
            <p className="text-caption text-muted-foreground">
              Solo se reparten pases de una compra ya pagada: una compra
              pendiente no habilita ninguna entrada.
            </p>
            <FormularioBeneficiario
              enviar={asignar}
              hayCupo={compra.disponibles > 0}
            />
          </section>

          <section
            aria-labelledby="beneficiarios-titulo"
            className="flex flex-col gap-3"
          >
            <h2
              id="beneficiarios-titulo"
              className="text-section-title text-foreground"
            >
              Quién usa cada pase
            </h2>
            <ListaBeneficiarios
              beneficiarios={compra.beneficiarios}
              revocar={revocar}
            />
          </section>
        </>
      ) : null}
    </div>
  );
}
