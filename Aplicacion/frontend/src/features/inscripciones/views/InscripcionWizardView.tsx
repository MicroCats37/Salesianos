"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Loader2,
  TriangleAlert,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { RouteHero } from "@/components/shell/RouteHero";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAltaInscripcion, useCatalogoPaquetes } from "../hooks";
import {
  AltaInscripcionSchema,
  type AltaInscripcionFormData,
} from "../schemas/alta-inscripcion.schema";
import type {
  CatalogoPaquetes,
  CompraInscripcion,
  EstadoInscripcion,
} from "../types/inscripcion.types";
import {
  construirPayloadAlta,
  type SolicitudAlta,
} from "../utils/inscripcion.payloads.utils";
import { PasoConfirmacion } from "../components/PasoConfirmacion";
import { PasoEquipos } from "../components/PasoEquipos";
import { PasoPaquete } from "../components/PasoPaquete";
import { PasoResumen } from "../components/PasoResumen";
import { WizardStepper, type WizardPaso } from "../components/WizardStepper";

export type { SolicitudAlta };

/**
 * The cause that declares that the inscription ALREADY EXISTED.
 *
 * The vocabulary of the cause is CLOSED in the backend
 * (`CausaOperativaInscripcion`: `INSCRIPCION_CREADA` /
 * `INSCRIPCION_REUTILIZADA`), so reading it is reading a declared fact and
 * not deriving a business value. The cause is ALSO printed verbatim, so a
 * cause that the backend adds in the future is shown instead of hidden.
 */
const CAUSA_INSCRIPCION_REUTILIZADA = "INSCRIPCION_REUTILIZADA";

/**
 * The answer of the server to the alta.
 *
 * `aceptada` is a registration that was just created; `recuperada` is the
 * registration that already existed and that the server returned again
 * instead of creating a second one.
 */
export type ResultadoAlta =
  | {
      tipo: "aceptada";
      inscripcion_id: string;
      compra: CompraInscripcion;
      causa_operativa: string;
    }
  | {
      tipo: "recuperada";
      inscripcion_id: string;
      compra: CompraInscripcion;
      causa_operativa: string;
    };

/**
 * An operation that the server already holds.
 *
 * It is the RECOVERY seam: when the responsible comes back to the wizard
 * with an inscription in flight, the page offers to continue THAT one
 * instead of creating a second.
 *
 * **The seam is not filled by the route**, and the reason is a gap of the
 * TARGET backend: there is no registered route that LISTS the inscriptions
 * of the responsible (`RT-IN-01 GET /inscripciones` is in the provisional
 * ledger and is NOT implemented). The recovery that IS reachable is the
 * idempotent alta itself: the retry answers with the inscription that
 * already exists, and the wizard then shows the recovery state instead of
 * offering the form again.
 */
export interface OperacionPendiente {
  inscripcion_id: string;
  compra: CompraInscripcion;
  causa_operativa: string;
}

export interface InscripcionWizardViewProps {
  /**
   * The edition whose catalogue is read. When it is omitted the server
   * resolves the edition with the frozen order (`FR-02` §2.2).
   */
  edicionId?: string;
  /**
   * An operation that the server already holds. No registered route
   * publishes it yet (see `OperacionPendiente`).
   */
  pendiente?: OperacionPendiente | null;
  /** The step the URL asks for. */
  pasoSolicitado?: string;
}

const PASOS: WizardPaso[] = [
  { id: 1, titulo: "Paquete", detalle: "El paquete que se contrata" },
  { id: 2, titulo: "Equipos", detalle: "Las disciplinas y los equipos" },
  { id: 3, titulo: "Resumen", detalle: "Lo que el servidor va a registrar" },
  { id: 4, titulo: "Confirmación", detalle: "Qué pasa al confirmar" },
];

function normalizarPaso(solicitado: string | undefined): number {
  const numero = Number.parseInt(solicitado ?? "1", 10);
  if (!Number.isFinite(numero)) return 1;
  if (numero < 1) return 1;
  if (numero > PASOS.length) return PASOS.length;
  return numero;
}

/**
 * InscripcionWizardView - SPORT-01, the creation of a registration.
 *
 * The wizard has FOUR steps, the ones the flow declares: the package, the
 * teams, the summary of what the server will do and the confirmation.
 *
 * Four rules govern the whole surface:
 *
 * 1. The step lives in the URL, so a step is RECOVERABLE: the visitor can
 *    come back to it, and the browser can reload it.
 * 2. Nothing is calculated in the browser: the price, the cupos, the
 *    eligibility and the capacity belong to the server.
 * 3. The catalogue is a REAL read (`RT-IN-12`) and the alta is a REAL write
 *    (`RT-IN-14`): there is no fixture and no invented route behind them.
 * 4. The 422 of the server reaches the control that owns the field: the
 *    error of the alta is re-thrown AS IT IS, never replaced by a generic
 *    message.
 */
export function InscripcionWizardView(props: InscripcionWizardViewProps) {
  const catalogo = useCatalogoPaquetes({ edicion_id: props.edicionId });
  const alta = useAltaInscripcion();

  const { mutateAsync } = alta;

  /**
   * The alta, as the server answered it.
   *
   * The reuse is READ from what the server declares: the boolean
   * `compra.reutilizada` and the cause of the answer. Nothing is derived.
   */
  const enviar = useCallback(
    async (solicitud: SolicitudAlta): Promise<ResultadoAlta> => {
      const respuesta = await mutateAsync(construirPayloadAlta(solicitud));

      const reutilizada =
        respuesta.data.compra.reutilizada === true ||
        respuesta.data.causa_operativa === CAUSA_INSCRIPCION_REUTILIZADA;

      return {
        tipo: reutilizada ? "recuperada" : "aceptada",
        inscripcion_id: respuesta.data.inscripcion.id,
        compra: respuesta.data.compra,
        causa_operativa: respuesta.data.causa_operativa,
      };
    },
    [mutateAsync],
  );

  const pendiente = props.pendiente ?? null;

  if (pendiente) {
    return <OperacionEnCurso pendiente={pendiente} />;
  }

  const mensajeError = catalogo.error ? catalogo.error.message : null;

  const estado: EstadoInscripcion = catalogo.isError
    ? "error"
    : catalogo.data
      ? "listo"
      : "sin-datos";

  if (estado === "error") {
    return (
      <div className="flex flex-col gap-6">
        <RouteHero
          pageId="SPORT-01"
          title="Crear una inscripción deportiva"
          description="El catálogo de la edición no se pudo leer."
        />
        <Alert className="border-destructive/45 bg-destructive/10">
          <TriangleAlert
            className="size-4 text-destructive"
            aria-hidden="true"
          />
          <AlertTitle className="text-foreground">
            No pudimos leer el catálogo de la edición
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            {mensajeError ??
              "El servicio de inscripciones no respondió. Vuelve a intentarlo en unos segundos."}
          </AlertDescription>
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => void catalogo.refetch()}
              className="min-h-11"
            >
              Reintentar
            </Button>
          </div>
        </Alert>
      </div>
    );
  }

  if (estado !== "listo" || !catalogo.data) {
    return <CatalogoEnCurso />;
  }

  return (
    <AsistenteInscripcion
      catalogo={catalogo.data}
      enviar={enviar}
      pasoSolicitado={props.pasoSolicitado}
    />
  );
}

/**
 * CatalogoEnCurso - the state of the wizard while the catalogue travels.
 *
 * It is a SKELETON with the geometry of the cards, and not an empty state:
 * the catalogue is coming, and saying "there is no catalogue" would be a lie.
 */
function CatalogoEnCurso() {
  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SPORT-01"
        title="Crear una inscripción deportiva"
        description="Estamos leyendo el catálogo de la edición."
      />

      <div
        className="flex flex-col gap-3"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <span className="sr-only">
          Cargando los paquetes disponibles de la edición
        </span>
        {[0, 1].map((indice) => (
          <div
            key={indice}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * OperacionEnCurso - the recovery of a pending operation.
 *
 * The server already holds an inscription for this responsible. The page
 * does NOT offer to create another one: it offers to continue the one that
 * exists.
 */
function OperacionEnCurso(props: { pendiente: OperacionPendiente }) {
  const pendiente = props.pendiente;

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SPORT-01"
        title="Ya hay una inscripción en curso"
        description="El servidor tiene una inscripción abierta para tu cuenta. No se crea una segunda: continúas la que ya existe."
      />

      <Alert className="border-info/45 bg-info/12">
        <TriangleAlert className="size-4 text-info" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          Tu inscripción está esperando el pago
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          Estado de la compra: {pendiente.compra.estado}. Los cupos se
          habilitan cuando el pago se confirme; hasta entonces la inscripción
          no tiene ningún cupo disponible.
        </AlertDescription>
      </Alert>
    </div>
  );
}

type Fase = "inicial" | "enviando" | "aceptada" | "recuperada" | "error-temporal";

/**
 * AsistenteInscripcion - the wizard itself.
 *
 * The form methods live HERE (Mode 4 of the GenericForm) and the steps read
 * what they own. The payload is assembled by the mapper of the feature: the
 * browser reports what the visitor chose and never calculates a business
 * value.
 */
function AsistenteInscripcion(props: {
  catalogo: CatalogoPaquetes;
  enviar: (solicitud: SolicitudAlta) => Promise<ResultadoAlta>;
  pasoSolicitado?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const [paso, setPaso] = useState(() => normalizarPaso(props.pasoSolicitado));
  const [fase, setFase] = useState<Fase>("inicial");
  const [resultado, setResultado] = useState<ResultadoAlta | null>(null);

  const methods = useForm<AltaInscripcionFormData>({
    resolver: zodResolver(AltaInscripcionSchema),
    defaultValues: {
      paquete_id: "",
      equipos: [{ disciplina_id: "", nombre: "" }],
    },
  });

  useEffect(() => {
    setPaso(normalizarPaso(props.pasoSolicitado));
  }, [props.pasoSolicitado]);

  const observacionPaquete = {
    control: methods.control,
    name: "paquete_id" as const,
  };
  const observacionEquipos = {
    control: methods.control,
    name: "equipos" as const,
  };

  const paqueteId = useWatch(observacionPaquete);
  const equipos = useWatch(observacionEquipos) ?? [];

  const paquetes = props.catalogo.paquetes;

  const paqueteSeleccionado = useMemo(
    () => paquetes.find((paquete) => paquete.id === paqueteId) ?? null,
    [paquetes, paqueteId],
  );

  const disciplinas = useMemo(
    () => paqueteSeleccionado?.disciplinas ?? [],
    [paqueteSeleccionado],
  );

  function irAlPaso(nuevo: number) {
    const destino = Math.min(Math.max(nuevo, 1), PASOS.length);
    setPaso(destino);
    router.replace((pathname ?? "/inscripcion") + "?paso=" + destino);
  }

  async function avanzar() {
    if (paso === 1) {
      const valido = await methods.trigger("paquete_id", { shouldFocus: true });
      if (!valido) return;
    }

    if (paso === 2) {
      const valido = await methods.trigger("equipos", { shouldFocus: true });
      if (!valido) return;
    }

    irAlPaso(paso + 1);
  }

  function retroceder() {
    irAlPaso(paso - 1);
  }

  async function alEnviar(datos: AltaInscripcionFormData) {
    setFase("enviando");

    const solicitud: SolicitudAlta = {
      edicion_id: props.catalogo.edicion_id,
      paquete_id: datos.paquete_id,
      equipos: datos.equipos.map((equipo) => ({
        disciplina_id: equipo.disciplina_id,
        nombre: equipo.nombre,
      })),
    };

    try {
      const respuesta = await props.enviar(solicitud);
      setResultado(respuesta);
      setFase(respuesta.tipo);
    } catch (error) {
      setFase("error-temporal");
      /**
       * The ORIGINAL error travels: the 422 of the server carries the field
       * errors, and the form needs them to mark the control that owns the
       * field (`contract/smart.md` §5.4 · FND-07).
       */
      throw error;
    }
  }

  if (fase === "aceptada" || fase === "recuperada") {
    return <ResultadoDelAlta resultado={resultado} fase={fase} />;
  }

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SPORT-01"
        title="Crear una inscripción deportiva"
        description="Cuatro pasos: el paquete que se contrata, los equipos que se anotan, el resumen de lo que registrará el servidor y la confirmación."
      />

      <GenericForm<AltaInscripcionFormData>
        schema={AltaInscripcionSchema}
        formMethods={methods}
        onSubmit={alEnviar}
        formClassName="flex flex-col gap-6"
      >
        {({ isSubmitting }) => (
          <div className="flex flex-col gap-6">
            <WizardStepper pasos={PASOS} actual={paso} />

            <div className="flex flex-col gap-4 rounded-[var(--radius-xl)] border border-border bg-surface-raised p-4 sm:p-6">
              {paso === 1 ? (
                <PasoPaquete
                  paquetes={paquetes}
                  cargando={false}
                  error={null}
                />
              ) : null}

              {paso === 2 ? <PasoEquipos disciplinas={disciplinas} /> : null}

              {paso === 3 ? (
                <PasoResumen
                  paquete={paqueteSeleccionado}
                  equipos={equipos}
                />
              ) : null}

              {paso === 4 ? (
                <PasoConfirmacion paquete={paqueteSeleccionado} />
              ) : null}
            </div>

            {fase === "error-temporal" ? (
              <Alert className="border-destructive/45 bg-destructive/10">
                <TriangleAlert
                  className="size-4 text-destructive"
                  aria-hidden="true"
                />
                <AlertTitle className="text-foreground">
                  No pudimos registrar la inscripción
                </AlertTitle>
                <AlertDescription className="text-muted-foreground">
                  Vuelve a intentarlo en unos segundos. Si el servidor ya
                  había creado la inscripción, al reintentar devuelve esa
                  misma y no se crea una segunda.
                </AlertDescription>
              </Alert>
            ) : null}

            <div className="flex flex-col-reverse items-stretch justify-between gap-3 sm:flex-row sm:items-center">
              <Button
                type="button"
                variant="ghost"
                onClick={retroceder}
                disabled={paso === 1 || isSubmitting}
                className="min-h-11 justify-start sm:justify-center"
              >
                <ArrowLeft className="size-4" aria-hidden="true" />
                Anterior
              </Button>

              {paso < PASOS.length ? (
                <Button
                  type="button"
                  onClick={avanzar}
                  disabled={isSubmitting}
                  className="min-h-11"
                >
                  Siguiente
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={isSubmitting || fase === "enviando"}
                  className="min-h-11"
                >
                  {isSubmitting || fase === "enviando" ? (
                    <>
                      <Loader2
                        className="size-4 animate-spin"
                        aria-hidden="true"
                      />
                      Registrando…
                    </>
                  ) : (
                    "Registrar la inscripción"
                  )}
                </Button>
              )}
            </div>
          </div>
        )}
      </GenericForm>
    </div>
  );
}

/**
 * ResultadoDelAlta - what happened after the registration.
 *
 * The inscription exists and the purchase is PENDING: the cupos are
 * enabled when the payment is confirmed and not before (RN-I02, QA-I01).
 * The page never says that there are cupos available.
 */
function ResultadoDelAlta(props: {
  resultado: ResultadoAlta | null;
  fase: "aceptada" | "recuperada";
}) {
  const resultado = props.resultado;
  const recuperado = props.fase === "recuperada";

  return (
    <div className="flex flex-col gap-6">
      <RouteHero
        pageId="SPORT-01"
        title="Tu inscripción quedó registrada"
        description="El siguiente paso es el pago. Los cupos se habilitan cuando se confirme."
      />

      <Alert className="border-info/45 bg-info/12">
        <TriangleAlert className="size-4 text-info" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          {recuperado
            ? "Ya existía esa inscripción"
            : "Inscripción registrada"}
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">
          {recuperado
            ? "El servidor tenía una inscripción para este paquete y la devolvió: no se ha creado una segunda ni se ha abierto otra compra."
            : "Se ha creado tu inscripción y su compra pendiente."}{" "}
          Estado de la compra: {resultado?.compra.estado}. Mientras el pago
          no se confirme, la inscripción no tiene ningún cupo disponible.
        </AlertDescription>
      </Alert>

      {resultado ? (
        <p className="text-caption text-muted-foreground">
          Causa de la respuesta: {resultado.causa_operativa}
        </p>
      ) : null}
    </div>
  );
}

/**
 * The error of a field, drawn once.
 *
 * The step that owns the field draws its own label and its own error, so
 * the message is never repeated (contract/smart.md 5.3).
 */
export function AvisoDeCampo(props: { mensaje: string }) {
  return (
    <p className="flex items-center gap-1.5 text-xs text-destructive">
      <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
      {props.mensaje}
    </p>
  );
}
