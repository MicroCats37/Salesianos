import { CompetenciaCuadroRuta } from "@/features/competencias/views";

/**
 * ADM-12 - Operar el cuadro de encuentros
 */
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <CompetenciaCuadroRuta id={id} />;
}
