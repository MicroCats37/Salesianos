import { CompetenciasListaRuta } from "@/features/competencias/views";

/**
 * ADM-10 - Seleccionar y administrar competencias
 *
 * Los filtros viven en la URL, así que la página lee la query string y la
 * pasa al contenedor. El contenedor es el que lee el dato y le entrega el
 * estado a la vista: la página sólo enruta.
 *
 * ## La lectura es del CLIENTE
 *
 * `GET /competencias` exige una sesión, y la lista se pide desde el
 * navegador con el patrón de TanStack Query: un cliente, una clave y un
 * hook (`salesianos-api-data`). La página NO pide el dato, de modo que
 * ninguna lectura viaja con una cookie de servidor que el backend no
 * reconozca.
 *
 * ## Los estados
 *
 * - mientras la ruta lee, la vista dibuja su esqueleto;
 * - si la lectura falla, la vista dibuja su estado de error CON la acción
 *   que la resuelve (reintentar);
 * - si la lectura llega vacía, la vista dibuja su estado vacío honesto.
 */
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{
    estado?: string | string[];
    categoria_id?: string | string[];
  }>;
}) {
  const { estado, categoria_id } = await searchParams;

  return (
    <CompetenciasListaRuta
      filtroEstado={primerValor(estado)}
      filtroCategoria={primerValor(categoria_id)}
    />
  );
}

/**
 * The value of a filter of the URL, when there is exactly one.
 *
 * A repeated parameter (`?estado=a&estado=b`) is NOT a filter: the route
 * accepts ONE state and ONE band, so the extra values are dropped instead
 * of being sent as a comma-separated list that the server does not know.
 */
function primerValor(valor: string | string[] | undefined): string | undefined {
  if (typeof valor === "string") return valor;
  if (Array.isArray(valor)) return valor[0];

  return undefined;
}
