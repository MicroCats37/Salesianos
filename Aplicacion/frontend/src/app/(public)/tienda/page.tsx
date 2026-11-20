import { TiendaRuta } from "@/features/marketplace/views";

/**
 * SHOP-01 - Elegir un producto del catálogo
 *
 * El filtro de la categoría vive en la URL, así que la página lo lee de la
 * query string y lo pasa a la vista.
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

  return <TiendaRuta categoriaActiva={valor("categoria")} />;
}
