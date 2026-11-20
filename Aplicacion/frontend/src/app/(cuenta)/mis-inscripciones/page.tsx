import { MisInscripcionesView } from "@/features/cuenta/views";

/**
 * ACCOUNT-02 - Listar tus inscripciones y su estado
 *
 * The filters live in the URL, so the page reads them from the query
 * string and hands them to the view. The page stays thin: it composes the
 * feature, it never filters by itself.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;

  const valor = (clave: string) => {
    const bruto = params[clave];
    return Array.isArray(bruto) ? bruto[0] : bruto;
  };

  return (
    <MisInscripcionesView
      filtros={{
        edicion: valor("edicion"),
        estado: valor("estado"),
      }}
    />
  );
}
