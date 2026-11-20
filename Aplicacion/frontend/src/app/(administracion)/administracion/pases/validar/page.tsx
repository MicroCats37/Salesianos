import { ValidarPaseRuta } from "@/features/validaciones/views";

/**
 * ADM-16 - Controlar el ingreso a la fiesta
 *
 * La página es SÓLO RUTEO: el contenedor (`ValidarPaseRuta`) es el que
 * habla con el backend y el que decide el estado de la pantalla.
 */
export default function Page() {
  return <ValidarPaseRuta />;
}
