import { MisInscripcionDetalleView } from "@/features/inscripciones/views";

/**
 * ACCOUNT-03 - Gestionar una inscripción, su pool y sus equipos
 *
 * La ruta sólo compone: el detalle vive en la feature de inscripciones,
 * que es la dueña del dominio. Los datos los publica el servidor y la
 * integración los entrega en API-02.
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <MisInscripcionDetalleView id={id} />;
}
