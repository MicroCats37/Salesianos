import { InscripcionWizardView } from "@/features/inscripciones/views";

/**
 * SPORT-01 - Crear una inscripción deportiva
 *
 * La ruta sólo compone: el asistente vive en la feature. El paso vive en
 * la URL (`?paso=`), así que un paso se puede recuperar y el navegador
 * puede recargarlo sin perder el sitio.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ paso?: string }>;
}) {
  const { paso } = await searchParams;

  return <InscripcionWizardView pasoSolicitado={paso} />;
}
