import {
  InscripcionClientShell,
  InscripcionWizardView,
} from "@/features/inscripciones/views";

/**
 * SPORT-01 - Crear una inscripción deportiva
 *
 * La superficie (el cristal y la luz de ambiente) es de la feature y el
 * asistente va dentro: la ruta sólo compone.
 *
 * La ruta vive en su propio grupo (`(inscripcion)`) porque el formulario es
 * una PÁGINA COMPLETA: con el sidebar de la cuenta el asistente quedaba
 * squeezed en una columna y la pantalla perdía su carácter de evento.
 */
export default function Page() {
  return (
    <InscripcionClientShell>
      <InscripcionWizardView />
    </InscripcionClientShell>
  );
}
