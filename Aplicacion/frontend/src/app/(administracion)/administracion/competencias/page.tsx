import { TorneoAdminRuta } from "@/features/competencias/publico/views/TorneoAdminRuta";

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
export default function Page() {
  return <TorneoAdminRuta />;
}
