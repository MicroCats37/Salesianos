import { ValidarEntregaRuta } from "@/features/validaciones/views";

/**
 * ADM-20 - Validar las recogidas
 *
 * La página es SÓLO RUTEO: el contenedor (`ValidarEntregaRuta`) es el que
 * habla con el backend y el que decide el estado de la pantalla.
 */
export default function Page() {
  return <ValidarEntregaRuta />;
}
