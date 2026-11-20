import { redirect } from "next/navigation";

/**
 * ADM-20 - Validar las recogidas
 *
 * Las recogidas se gestionan dentro de Tienda; esta ruta se mantiene solo
 * para redirigir enlaces existentes.
 */
export default function Page() {
  redirect("/administracion/marketplace#recogidas");
}
