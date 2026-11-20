"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { gsap } from "gsap";
import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  CheckCircle2,
  Loader2,
  Package,
  Receipt,
  RotateCcw,
  ShieldCheck,
  TriangleAlert,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { FestBrandHeader } from "@/components/brand/FestBrandHeader";
import { GenericForm } from "@/components/genericForm/GenericForm";
import { RouteHero } from "@/components/shell/RouteHero";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { handleApiError, notify } from "@/errors";
import { useGSAP } from "@/hooks/system/use-gsap";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { PasoBanner } from "../components/PasoBanner";
import { PasoConfirmacion } from "../components/PasoConfirmacion";
import {
  DECLARACIONES_INICIALES,
  type Declaraciones,
  PasoDeclaraciones,
} from "../components/PasoDeclaraciones";
import { PasoEquipos } from "../components/PasoEquipos";
import { PasoPaquete } from "../components/PasoPaquete";
import { PasoPromocion } from "../components/PasoPromocion";
import { PasoResumen } from "../components/PasoResumen";
import { type WizardPaso, WizardStepper } from "../components/WizardStepper";
import { useAltaInscripcion, useCatalogoPaquetes } from "../hooks";
import {
  useCatalogoCategorias,
  useCatalogoPromociones,
} from "../hooks/useCatalogo";
import { useCotizacion } from "../hooks/useCotizacion";
import {
  type AltaInscripcionFormData,
  AltaInscripcionSchema,
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
  {
    id: 1,
    titulo: "Paquete",
    detalle: "El paquete y las personas",
    Icono: Package,
  },
  {
    id: 2,
    titulo: "Promoción",
    detalle: "La cohorte a la que perteneces",
    Icono: Users,
  },
  {
    id: 3,
    titulo: "Equipos",
    detalle: "Las disciplinas y los equipos",
    Icono: ShieldCheck,
  },
  {
    id: 4,
    titulo: "Resumen",
    detalle: "Lo que el servidor va a registrar",
    Icono: Receipt,
  },
  {
    id: 5,
    titulo: "Confirmación",
    detalle: "Qué pasa al confirmar",
    Icono: BadgeCheck,
  },
];

/**
 * What each step asks for.
 *
 * It is the band of colour of the previous frontend: the visitor always
 * knows what is being decided NOW, before the fields of the step.
 */
const BANDERAS: Record<
  number,
  { titulo: string; detalle: string; Icono: LucideIcon }
> = {
  1: {
    titulo: "Paso 1 · Paquete",
    detalle:
      "Empieza eligiendo el paquete que mejor se adapta a tu promoción. Esto define cuántos cupos se compran y cuántas personas se anotan.",
    Icono: Package,
  },
  2: {
    titulo: "Paso 2 · Promoción",
    detalle:
      "Selecciona tu promoción (con fusión opcional). El comité la usa para asignar la categoría deportiva de cada equipo.",
    Icono: Users,
  },
  3: {
    titulo: "Paso 3 · Equipos",
    detalle:
      "Declara un equipo por cada disciplina que contracting. Las personas se agregan después, desde el detalle de la inscripción.",
    Icono: ShieldCheck,
  },
  4: {
    titulo: "Paso 4 · Resumen",
    detalle:
      "Revisa lo que el servidor va a registrar. El precio lo resuelve el servidor contra el catálogo vigente.",
    Icono: Receipt,
  },
  5: {
    titulo: "Paso 5 · Confirmación",
    detalle:
      "Último paso: confirma y el servidor registra la inscripción y abre la compra pendiente.",
    Icono: BadgeCheck,
  },
};

/**
 * The delay before asking the server for the quotation of a new quantity.
 *
 * The quotation is a remote read of the price, and the visitor moves the
 * stepper in bursts: without the delay every click would be a request.
 */
const COTIZACION_DELAY_MS = 400;

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
 * The wizard has FIVE steps, the ones the flow declares: the package and the
 * people, the cohort, the teams, the summary of what the server will do and
 * the confirmation.
 *
 * Four rules govern the whole surface:
 *
 * 1. The step lives in the URL, so a step is RECOVERABLE: the visitor can
 *    come back to it, and the browser can reload it.
 * 2. Nothing is calculated in the browser: the price, the total, the
 *    category, the cupos, the eligibility and the capacity belong to the
 *    server. The only figure that the browser owns is the QUANTITY, which is
 *    the decision of the visitor.
 * 3. The catalogue is a REAL read (`RT-IN-12`, `RT-IN-15`, `RT-IN-16`) and
 *    the alta is a REAL write (`RT-IN-14`): there is no fixture and no
 *    invented route behind them.
 * 4. The 422 of the server reaches the control that owns the field: the
 *    error of the alta is re-thrown AS IT IS, never replaced by a generic
 *    message.
 */
export function InscripcionWizardView(props: InscripcionWizardViewProps) {
  const catalogo = useCatalogoPaquetes({ edicion_id: props.edicionId });
  const promociones = useCatalogoPromociones({ edicion_id: props.edicionId });
  const categorias = useCatalogoCategorias({ edicion_id: props.edicionId });
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

  /**
   * The message of the server survives the automatic retry.
   *
   * `failureReason` is the LAST failure of the read: while the client retries
   * in the background, the surface already shows the words of the server
   * instead of hiding them behind a skeleton (`SH-03` S-04).
   */
  const mensajeError =
    catalogo.failureReason?.message ??
    (catalogo.error ? catalogo.error.message : null);

  /**
   * The honest state appears as soon as the read has FAILED once.
   *
   * The client retries a 5xx in the background, but the surface never hides
   * the failure of the server behind a loading skeleton: the message of the
   * backend and the action that resolves it are shown at once
   * (`SH-03` S-04).
   */
  const estado: EstadoInscripcion =
    catalogo.isError || catalogo.failureCount > 0
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
      promociones={promociones}
      categorias={categorias}
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

      <output
        className="flex flex-col gap-3"
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
      </output>
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
          Estado de la compra: {pendiente.compra.estado}. Los cupos se habilitan
          cuando el pago se confirme; hasta entonces la inscripción no tiene
          ningún cupo disponible.
        </AlertDescription>
      </Alert>
    </div>
  );
}

type Fase =
  | "inicial"
  | "enviando"
  | "aceptada"
  | "recuperada"
  | "error-temporal";

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
  promociones: ReturnType<typeof useCatalogoPromociones>;
  categorias: ReturnType<typeof useCatalogoCategorias>;
  enviar: (solicitud: SolicitudAlta) => Promise<ResultadoAlta>;
  pasoSolicitado?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const [paso, setPaso] = useState(() => normalizarPaso(props.pasoSolicitado));
  const [fase, setFase] = useState<Fase>("inicial");
  const [resultado, setResultado] = useState<ResultadoAlta | null>(null);

  /**
   * The three declarations of the last step.
   *
   * They live in the LOCAL state of the wizard: the backend records the
   * acceptances per person, so they are not fields of the registration.
   * They are a CONDITION to send.
   */
  const [declaraciones, setDeclaraciones] = useState(DECLARACIONES_INICIALES);
  const declaracionesCompletas =
    declaraciones.bases && declaraciones.aptitudFisica && declaraciones.imagen;

  /**
   * The direction of the step transition.
   *
   * It is a REF and not a state: the animation has to know the direction in
   * the very same commit in which the step changes, and a state would arrive
   * one render later.
   */
  const direccion = useRef(1);
  const contenidoRef = useRef<HTMLDivElement>(null);

  /**
   * The transition BETWEEN the steps.
   *
   * The content of the step slides in from the side the visitor came from:
   * going forward comes from the right, going back from the left. It is a
   * REVEAL (opacity and a translation): the step never animates its height,
   * so the layout does not jump underneath the visitor.
   *
   * The step that is already in the DOM does NOT animate on the first paint:
   * the server already sent it painted, and animating it would produce a
   * flash of content that appears and disappears.
   */
  useGSAP(
    () => {
      const contenido = contenidoRef.current;
      if (!contenido) return;

      const media = gsap.matchMedia();

      media.add(
        { motionReducido: "(prefers-reduced-motion: reduce)" },
        (contexto) => {
          const condiciones = contexto.conditions as {
            motionReducido?: boolean;
          };

          if (condiciones.motionReducido) {
            gsap.set(contenido, { autoAlpha: 1, x: 0, clearProps: "all" });
            return;
          }

          const linea = gsap.timeline({ defaults: { ease: "power3.out" } });

          linea.fromTo(
            contenido,
            { autoAlpha: 0, x: direccion.current * 24, filter: "blur(4px)" },
            {
              autoAlpha: 1,
              x: 0,
              filter: "blur(0px)",
              duration: 0.4,
              clearProps: "opacity,visibility,transform,filter",
            },
          );
        },
      );

      return () => {
        media.revert();
      };
    },
    { scope: contenidoRef, dependencies: [paso] },
  );
  /**
   * The field errors of the LAST answer of the server.
   *
   * A 422 names the field it rejected, and that field may live in another
   * step of the wizard. The wizard therefore announces them where they can be
   * read at once, and the control that owns the field shows them too when
   * the visitor goes back to its step (`SH-02` A11Y-05).
   */
  const [erroresDelServidor, setErroresDelServidor] = useState<
    Record<string, string>
  >({});

  const methods = useForm<AltaInscripcionFormData>({
    resolver: zodResolver(AltaInscripcionSchema),
    defaultValues: {
      paquete_id: "",
      promocion_id: "",
      fusion_promocion_id: null,
      cantidad: 1,
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
  const observacionCantidad = {
    control: methods.control,
    name: "cantidad" as const,
  };
  const observacionPromocion = {
    control: methods.control,
    name: "promocion_id" as const,
  };
  const observacionFusion = {
    control: methods.control,
    name: "fusion_promocion_id" as const,
  };
  const observacionEquipos = {
    control: methods.control,
    name: "equipos" as const,
  };

  const paqueteId = useWatch(observacionPaquete);
  const cantidad = useWatch(observacionCantidad);
  const promocionId = useWatch(observacionPromocion);
  const fusionPromocionId = useWatch(observacionFusion);
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

  const promociones = useMemo(
    () => props.promociones.data?.promociones ?? [],
    [props.promociones.data],
  );

  const categorias = useMemo(
    () => props.categorias.data?.categorias ?? [],
    [props.categorias.data],
  );

  const promocionSeleccionada = useMemo(
    () => promociones.find((promocion) => promocion.id === promocionId) ?? null,
    [promociones, promocionId],
  );

  const fusionSeleccionada = useMemo(
    () =>
      promociones.find((promocion) => promocion.id === fusionPromocionId) ??
      null,
    [promociones, fusionPromocionId],
  );

  /**
   * The commercial minimum of the chosen package.
   *
   * It is the floor of the quantity: the quotation is only asked for a
   * quantity that respects it, because a quote below the minimum is a
   * request that the server rejects (`RN-C02`).
   */
  const minimoCantidad = paqueteSeleccionado?.minimo_compra_inicial ?? 1;

  /**
   * The quotation of the selected package and the selected quantity.
   *
   * It lives in the CONTAINER and not in the step: the step renders it, but
   * the payload of the alta needs its `version` (the token of the
   * concurrency check), so there is ONE instance for the whole wizard.
   */
  const cotizacion = useCotizacion();

  /**
   * The quotation follows the package AND the quantity.
   *
   * The quotation of the previous combination is dropped BEFORE the new one
   * is asked for, so the panel never shows the price of another quantity
   * while the new answer travels.
   */
  useEffect(() => {
    if (!paqueteId || !cantidad || cantidad < minimoCantidad) return;

    cotizacion.invalidar();
    const temporizador = setTimeout(() => {
      cotizacion.cotizar(paqueteId, cantidad);
    }, COTIZACION_DELAY_MS);

    return () => clearTimeout(temporizador);
  }, [
    paqueteId,
    cantidad,
    minimoCantidad,
    cotizacion.cotizar,
    cotizacion.invalidar,
  ]);

  function irAlPaso(nuevo: number) {
    const destino = Math.min(Math.max(nuevo, 1), PASOS.length);
    direccion.current = destino > paso ? 1 : -1;
    setPaso(destino);
    router.replace(`${pathname ?? "/inscripcion"}?paso=${destino}`);
  }

  async function avanzar() {
    if (paso === 1) {
      const valido = await methods.trigger(["paquete_id", "cantidad"], {
        shouldFocus: true,
      });
      if (!valido) return;
    }

    if (paso === 2) {
      const valido = await methods.trigger("promocion_id", {
        shouldFocus: true,
      });
      if (!valido) return;
    }

    if (paso === 3) {
      const valido = await methods.trigger("equipos", { shouldFocus: true });
      if (!valido) return;
    }

    irAlPaso(paso + 1);
  }

  function retroceder() {
    irAlPaso(paso - 1);
  }

  function cambiarDeclaracion(clave: keyof Declaraciones, valor: boolean) {
    setDeclaraciones((previas) => ({ ...previas, [clave]: valor }));
  }

  async function alEnviar(datos: AltaInscripcionFormData) {
    /**
     * The declarations are checked FIRST: the visitor must not be surprised
     * by a rejection of the server when the conditions were visible.
     */
    if (!declaracionesCompletas) {
      notify.error("Debes aceptar las tres declaraciones para continuar");
      return;
    }

    setFase("enviando");

    /**
     * The concurrency token of the quotation travels ONLY when there is a
     * quotation of THIS package and THIS quantity, and the price and the
     * total NEVER travel: the server resolves the money again against the
     * catalogue in force (`RN-C02`).
     */
    const cotizacionActual = cotizacion.cotizacion;
    const esDelPaquete =
      cotizacionActual !== null &&
      cotizacionActual.paquete_id === datos.paquete_id &&
      cotizacionActual.cantidad_cotizada === datos.cantidad;

    const solicitud: SolicitudAlta = {
      edicion_id: props.catalogo.edicion_id,
      paquete_id: datos.paquete_id,
      promocion_id: datos.promocion_id,
      cantidad: datos.cantidad,
      fusion_promocion_id: datos.fusion_promocion_id
        ? datos.fusion_promocion_id
        : null,
      cotizacion_version: esDelPaquete ? cotizacionActual.version : undefined,
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
       * The field errors of the 422 are read BEFORE the error travels: they
       * name the fields the server rejected, and the wizard announces them
       * where they can be read at once.
       */
      setErroresDelServidor(handleApiError(error).fieldErrors ?? {});
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
      {/*
       * The lockup of the brand, centered, as the previous frontend had it:
       * the crest, the wordmark and the place of the visitor in the flow.
       * The title of the route stays in the document for the assistive
       * technology and for the search engine.
       */}
      <div className="flex flex-col items-center gap-3 pb-1">
        <h1 className="sr-only">
          Crear una inscripción deportiva · Paso {paso} de {PASOS.length}
        </h1>
        <FestBrandHeader
          variant="onLight"
          size="sm"
          subtitle={`Preinscripción · Paso ${paso} de ${PASOS.length}`}
        />
      </div>

      <GenericForm<AltaInscripcionFormData>
        schema={AltaInscripcionSchema}
        formMethods={methods}
        onSubmit={alEnviar}
        formClassName="flex flex-col gap-6"
      >
        {({ isSubmitting }) => (
          <div className="flex flex-col gap-6">
            <WizardStepper pasos={PASOS} actual={paso} />

            {BANDERAS[paso] ? (
              <PasoBanner
                titulo={BANDERAS[paso].titulo}
                detalle={BANDERAS[paso].detalle}
                Icono={BANDERAS[paso].Icono}
              />
            ) : null}

            {Object.keys(erroresDelServidor).length > 0 ? (
              <Alert className="border-destructive/45 bg-destructive/10">
                <TriangleAlert
                  className="size-4 text-destructive"
                  aria-hidden="true"
                />
                <AlertTitle className="text-foreground">
                  El servidor rechazó{" "}
                  {Object.keys(erroresDelServidor).length === 1
                    ? "este campo"
                    : "estos campos"}
                </AlertTitle>
                <AlertDescription>
                  <ul className="flex flex-col gap-0.5">
                    {Object.entries(erroresDelServidor).map(
                      ([campo, mensaje]) => (
                        <li
                          key={campo}
                          className="text-caption text-muted-foreground"
                        >
                          {mensaje}
                        </li>
                      ),
                    )}
                  </ul>
                </AlertDescription>
              </Alert>
            ) : null}

            <div
              ref={contenidoRef}
              className="relative flex flex-col gap-4 overflow-hidden rounded-[var(--radius-xl)] border border-border bg-surface-raised p-4 sm:p-6"
            >
              {/*
               * The rule of the brand along the top edge of the panel: it
               * says that this is a step of the festival and not another box
               * of the back office.
               */}
              <span
                aria-hidden="true"
                className="rule-gold absolute inset-x-0 top-0 h-1"
              />
              {paso === 1 ? (
                <PasoPaquete
                  paquetes={paquetes}
                  cargando={false}
                  error={null}
                  cotizacion={cotizacion.cotizacion}
                  cotizacionCargando={cotizacion.estaCargando}
                  cotizacionError={
                    cotizacion.hayError
                      ? (cotizacion.error?.message ?? null)
                      : null
                  }
                />
              ) : null}

              {paso === 2 ? (
                <PasoPromocion
                  promociones={promociones}
                  categorias={categorias}
                />
              ) : null}

              {paso === 3 ? <PasoEquipos disciplinas={disciplinas} /> : null}

              {paso === 4 ? (
                <PasoResumen
                  paquete={paqueteSeleccionado}
                  equipos={equipos}
                  promocion={promocionSeleccionada}
                  fusionPromocion={fusionSeleccionada}
                  cantidad={cantidad}
                  cotizacion={cotizacion.cotizacion}
                />
              ) : null}

              {paso === 5 ? (
                <div className="flex flex-col gap-5">
                  {/*
                   * The declarations come from the previous frontend:
                   * they are a CONDITION to send, not a field of the
                   * registration, and they are checked before the payload
                   * leaves the browser.
                   */}
                  <PasoDeclaraciones
                    declaraciones={declaraciones}
                    onCambiar={cambiarDeclaracion}
                    completas={declaracionesCompletas}
                  />

                  <PasoConfirmacion
                    paquete={paqueteSeleccionado}
                    promocion={promocionSeleccionada}
                    cantidad={cantidad}
                    cotizacion={cotizacion.cotizacion}
                  />
                </div>
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
                  Vuelve a intentarlo en unos segundos. Si el servidor ya había
                  creado la inscripción, al reintentar devuelve esa misma y no
                  se crea una segunda.
                </AlertDescription>
              </Alert>
            ) : null}

            {/*
             * The action bar.
             *
             * It is a RAISED band: the navigation of the wizard is a single
             * object and not two buttons floating in the page. Below 640 the
             * two actions are stacked, so both keep a 44px touch target.
             */}
            <div className="flex flex-col-reverse items-stretch justify-between gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-recessed p-3 sm:flex-row sm:items-center sm:p-4">
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
                  className="min-h-11 rounded-full bg-accent font-bold text-accent-foreground shadow-[var(--elevation-md)] transition-colors duration-(--motion-duration-fast) hover:bg-accent/90"
                >
                  Siguiente
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={isSubmitting || fase === "enviando"}
                  className="min-h-11 rounded-full bg-success font-bold text-success-foreground shadow-[var(--elevation-md)] transition-colors duration-(--motion-duration-fast) hover:bg-success/90"
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
      {/*
       * The lockup of the brand: the registration is a MOMENT of the event
       * and it ends with the same mark that it started with.
       */}
      <div className="flex flex-col items-center gap-3 pb-1">
        <FestBrandHeader
          variant="onLight"
          size="sm"
          subtitle={
            recuperado ? "Ya tenías esta inscripción" : "Inscripción registrada"
          }
        />
      </div>

      <section className="flex flex-col gap-6 rounded-[var(--radius-xl)] border border-border bg-card/95 p-6 shadow-[var(--elevation-md)] sm:p-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <span
            className={cn(
              "flex size-16 items-center justify-center rounded-full",
              recuperado
                ? "bg-info/15 text-info"
                : "bg-success/15 text-success",
            )}
          >
            {recuperado ? (
              <RotateCcw className="size-6" aria-hidden="true" />
            ) : (
              <CheckCircle2 className="size-6" aria-hidden="true" />
            )}
          </span>

          <h2 className="font-heading text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {recuperado
              ? "Ya existía esa inscripción"
              : "Tu inscripción quedó registrada"}
          </h2>

          <p className="max-w-measure text-sm leading-relaxed text-muted-foreground">
            {recuperado
              ? "El servidor ya tenía una inscripción para este paquete y te la devolvió: no se ha creado una segunda ni se ha abierto otra compra."
              : "Se ha creado tu inscripción y su compra pendiente."}{" "}
            El siguiente paso es el pago: los cupos se habilitan cuando se
            confirme y no antes.
          </p>
        </div>

        <dl className="grid gap-3 rounded-[var(--radius-lg)] bg-muted/50 p-4 sm:grid-cols-3">
          <Dato
            termino="Estado de la compra"
            valor={resultado?.compra.estado ?? "—"}
          />
          <Dato
            termino="Causa de la respuesta"
            valor={resultado?.causa_operativa ?? "—"}
          />
          <Dato termino="Cupos disponibles" valor="Se habilitan con el pago" />
        </dl>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {resultado ? (
            <Button
              asChild
              className="min-h-11 rounded-full bg-primary px-6 font-bold text-primary-foreground"
            >
              <Link
                href={RUTAS.cuenta.misInscripcionesDetalle(
                  resultado.inscripcion_id,
                )}
              >
                Ver mi inscripción
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          ) : null}

          <Button
            asChild
            variant="outline"
            className="min-h-11 rounded-full px-6 font-bold"
          >
            <Link href={RUTAS.cuenta.misInscripciones}>Mis inscripciones</Link>
          </Button>

          <Button
            asChild
            variant="ghost"
            className="min-h-11 rounded-full px-6 font-bold"
          >
            <Link href={RUTAS.publico.inicio}>Ver el festival</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}

/**
 * One fact of the confirmation, drawn in the same grammar as the summary.
 */
function Dato({ termino, valor }: { termino: string; valor: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-eyebrow-brand text-muted-foreground">{termino}</dt>
      <dd className="text-sm font-semibold text-foreground">{valor}</dd>
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
