import { MisComprasView } from "@/features/cuenta/views";

/**
 * ACCOUNT-04 - Listar tus compras
 *
 * The filters live in the URL, so the page reads them from the query
 * string and hands them to the view.
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

  return <MisComprasView filtros={{ origen: valor("origen") }} />;
}
