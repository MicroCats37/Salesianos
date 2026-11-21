import { VideoDetalleRuta } from "@/features/videos/views";

/** Public live broadcast detail. */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <VideoDetalleRuta id={id} />;
}
