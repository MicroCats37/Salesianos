import { CalendarDays, MapPin, Timer } from "lucide-react";
import Link from "next/link";
import { FestivalPublicPage } from "@/components/shell/FestivalPublicPage";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import { FESTIVAL, SEDE, VENTAS } from "@/features/portada/fixtures/festival";
import { RUTAS } from "@/lib/routes";
import { EdicionActualPanel } from "../components/EdicionActualPanel";
import { IndiceInformacion } from "../components/IndiceInformacion";

/**
 * The dates are printed in the local time of the event.
 *
 * The time zone is FIXED on purpose: the server and the browser must print
 * the same day, and Lima does not observe daylight saving time.
 */
const FECHA = new Intl.DateTimeFormat("es-PE", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "America/Lima",
});

/**
 * The sections of the page.
 *
 * The index and the content read the SAME list, so an anchor can never
 * point to a section that does not exist (`RB-01` PUB-02).
 */
const SECCIONES = [
  { id: "lugar", titulo: "Dónde y cuándo nos vemos" },
  { id: "ventanas", titulo: "Cuándo se puede inscribir" },
  { id: "programa", titulo: "El programa y las disciplinas" },
] as const;

/**
 * PUB-02 - the edition, the disciplines and the rules.
 *
 * The date, the venue and the sales windows are the CONFIGURATION of the
 * product: they are not a row in a table and they do not come from a server.
 *
 * The EDITION itself — its name, its year, its dates and the modules it has
 * enabled — is what the backend publishes, and it is read from
 * `GET /ediciones/actual` (`RT-ED-01`) by `EdicionActualPanel`. The frontend
 * never resolves the edition by itself and never draws an example edition as
 * if it were the current one.
 *
 * What is still not published - the programme and the disciplines of this
 * edition - is said to be missing, in the section that will hold it.
 */
export function InformacionView() {
  return (
    <FestivalPublicPage
      eyebrow="INFORMACIÓN / SALESIANOS FEST"
      title={["TODO LO QUE", "NECESITAS", "SABER."]}
      highlighted="SABER."
      description={`${FESTIVAL.claim}. Encuentra la fecha, sede, programa y ventanas de inscripción de la edición.`}
    >
      <div className="grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)] lg:items-start">
        <IndiceInformacion
          secciones={SECCIONES.map((seccion) => ({ ...seccion }))}
          className="lg:sticky lg:top-20"
        />

        <div className="flex flex-col gap-10">
          <section id="lugar" className="flex scroll-mt-24 flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className="rule-gold block h-0.5 w-10 rounded-full"
                aria-hidden="true"
              />
              <h2 className="text-section-title text-foreground">
                Dónde y cuándo nos vemos
              </h2>
              <p className="max-w-measure text-lead text-muted-foreground">
                La sede y los horarios de la edición, con la ventana de
                inscripción de cada etapa.
              </p>
            </div>

            <ItemGroup className="gap-2">
              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <CalendarDays
                    className="size-4 text-primary"
                    aria-hidden="true"
                  />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>{FESTIVAL.fechaEvento}</ItemTitle>
                  <ItemDescription>
                    La jornada empieza el sábado por la mañana.
                  </ItemDescription>
                </ItemContent>
              </Item>

              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <MapPin className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>{SEDE.nombre}</ItemTitle>
                  <ItemDescription>
                    {SEDE.direccion}. {SEDE.bienvenida}
                  </ItemDescription>
                </ItemContent>
              </Item>
            </ItemGroup>

            <EdicionActualPanel />
          </section>

          <section id="ventanas" className="flex scroll-mt-24 flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className="rule-gold block h-0.5 w-10 rounded-full"
                aria-hidden="true"
              />
              <h2 className="text-section-title text-foreground">
                Cuándo se puede inscribir
              </h2>
              <p className="max-w-measure text-lead text-muted-foreground">
                Las cuatro ventanas de la edición. Cada una abre y cierra con la
                fecha que define la organización.
              </p>
            </div>

            <ItemGroup className="gap-2">
              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <Timer className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Preventa</ItemTitle>
                  <ItemDescription>
                    Hasta el {FECHA.format(new Date(VENTAS.preventaHasta))}.
                  </ItemDescription>
                </ItemContent>
              </Item>

              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <Timer className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Ventana regular</ItemTitle>
                  <ItemDescription>
                    Del {FECHA.format(new Date(VENTAS.regularDesde))} al{" "}
                    {FECHA.format(new Date(VENTAS.regularHasta))}.
                  </ItemDescription>
                </ItemContent>
              </Item>

              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <Timer className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Inscripción extemporánea</ItemTitle>
                  <ItemDescription>
                    Desde el {FECHA.format(new Date(VENTAS.extemporaneaDesde))}.
                  </ItemDescription>
                </ItemContent>
              </Item>

              <Item variant="outline" size="sm">
                <ItemMedia variant="icon">
                  <Timer className="size-4 text-primary" aria-hidden="true" />
                </ItemMedia>
                <ItemContent>
                  <ItemTitle>Cierre de inscripciones</ItemTitle>
                  <ItemDescription>
                    El {FECHA.format(new Date(VENTAS.inscripcionCierra))}.
                  </ItemDescription>
                </ItemContent>
              </Item>
            </ItemGroup>

            <div>
              <Button asChild className="min-h-11">
                <Link href={RUTAS.cuenta.inscripcion}>
                  Crear una inscripción
                </Link>
              </Button>
            </div>
          </section>

          <section id="programa" className="flex scroll-mt-24 flex-col gap-4">
            <div className="flex flex-col gap-2">
              <span
                className="rule-gold block h-0.5 w-10 rounded-full"
                aria-hidden="true"
              />
              <h2 className="text-section-title text-foreground">
                El programa y las disciplinas
              </h2>
            </div>
            <RouteEmptyState
              icon={CalendarDays}
              title="El programa publicado todavía no está disponible aquí"
              description="Las categorías y las disciplinas de esta edición las publica el catálogo del backend. La portada ya las muestra con su respaldo estático; esta página aloja la versión editorial, que se completará cuando el catálogo se conecte a esta ruta."
            />
          </section>
        </div>
      </div>
    </FestivalPublicPage>
  );
}
