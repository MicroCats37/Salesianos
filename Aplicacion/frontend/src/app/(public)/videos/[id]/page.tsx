import { VideoDetalleRuta } from "@/features/videos/views";

/**
 * VID-02 - Ver un video de la sala de proyección.
 *
 * El identificador del video es su identidad en la URL, así que la página lo
 * lee de los parámetros y lo entrega al contenedor.
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <VideoDetalleRuta id={id} />;
}
