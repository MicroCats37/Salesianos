# Frontend 02 — Fichas de páginas públicas, identidad e inscripciones

**Rutas propuestas sujetas a revisión.** Este documento define intención y UX, no componentes exactos obligatorios.

## PUB-01 — `/`: portada de la edición

**Actor:** visitante. **Objetivo:** entender qué es Salesianos FEST y actuar sin navegar por páginas redundantes.

**Bloques:** héroe con edición/fechas, actividades habilitadas, disciplinas, paquetes destacados con CTA, pases, tienda (si habilitada), patrocinadores, preguntas frecuentes y pie. Los datos comerciales provienen del servidor; sin precio real, no mostrar precio ficticio.

**Acciones:** abrir información, iniciar inscripción, comprar entrada, explorar tienda, iniciar sesión. **Estados:** edición no publicada (mensaje), módulo no habilitado (ocultar sección), carga/error de catálogo (retry; no fallback inventado). **Aceptación:** un visitante llega a la tarea principal en máximo 2 navegaciones desde portada.

## PUB-02 — `/informacion`: detalles de la edición

**Objetivo:** reglamento/cronograma/categorías y condiciones accesibles. Evitar otra landing visual completa. **Bloques:** navegación por anclas reales, contenido organizado por temas, CTA consistente. **Aceptación:** las anclas del menú llevan a secciones presentes; no dos catálogos client-side para los mismos paquetes.

## AUTH-01 — `/login`

**Actor:** persona que necesita cuenta de responsable o administrador. **Bloques:** identificación, contraseña/credencial que determine auth, recuperación de acceso (según arquitectura), mensaje específico de error, enlaces a registro. **Resultado:** usuario normal → área personal; administrador → panel. La autenticación se verifica en servidor, no en un store/cookie de frontend.

**No obligar login para comprar pase/tienda** cuando esté habilitada compra invitada.

## AUTH-02 — `/registro`

**Bloques:** tipo/documento, búsqueda local→RENIEC, datos confirmables, contacto, credenciales, consentimientos reales. **Actuación:** buscar DNI no crea necesariamente Persona; persistir en registro exitoso. **Errores:** DNI no encontrado, fuente temporalmente indisponible, documento ya vinculado a cuenta, validación de email, duplicidad.

**Aceptación:** no duplicar personas existentes ni crear un usuario para cada participante deportivo.

## ACCOUNT-01 — `/mi-cuenta`

**Objetivo:** iniciar la tarea personal, no mostrar todas las tablas del sistema. **Secciones:** “Mis inscripciones”, “Mis compras”, “Mis entradas” si existen. CTA “Nueva inscripción”; estado vacío con acciones. Evitar términos de Izipay.

## ACCOUNT-02 — `/mis-inscripciones`

**Lista de tarjetas/filas:** edición, paquete, promoción, equipos, estado comprensible, cupos disponibles, siguiente acción (“Completar pago”, “Asignar participantes”, “Ver equipo”). **Filtro:** edición, estado; búsqueda local solo si útil. **Acciones:** abrir inscripción, nueva inscripción. **Estados:** sin inscripciones, pago en verificación, cierre de modificación, error de conexión.

## SPORT-01 — `/inscripcion`: wizard deportivo

**Etapas recomendadas:**

1. **Edición/paquete.** Elegir solo paquetes habilitados; explicar condiciones, beneficios, cantidad mínima, disciplinas y precio confirmado por backend.
2. **Equipos.** Indicar cuántos equipos y disciplinas permite el paquete; mostrar validación clara (nombre, disciplina, categoría, promoción) antes de pasar.
3. **Cupos y resumen.** Elegir cantidad inicial, ver importe final, beneficios incluidos y responsables.
4. **Confirmación/compra.** Crear inscripción y compra inicial; abrir pago, permitir recuperar operación pendiente sin duplicar.

**No pedir toda la plantilla antes del pago** si el flujo aprobado permite asignarla después desde el pool. **Flujos:** FL-02, FL-03. **Aceptación:** una inscripción creada no se duplica al recargar; se sabe qué falta antes de poder jugar.

## ACCOUNT-03 — `/mis-inscripciones/[id]`: detalle del responsable

**Cabecera:** edición, paquete, estado de inscripción, resumen operativo y siguiente acción.

**Secciones visibles:**

- `Pool`: Cupos pagados, asignados activos, disponibles; botón “Agregar cupos”.
- `Equipos`: Tarjetas por disciplina/categoría con jugadores vs mínimo/máximo y estado explicado.
- `Participantes`: buscar persona, agregar al pool, asignar, mover y retirar con confirmación.
- `Compras`: inicial/ampliaciones, estado y acceso a pago pendiente.
- `Beneficios`: qué está incluido y cuáles dependen de asignación (FIesta, BOX) sin mezclar con cupos.

**Estados de bloqueo:** no hay cupos pagados, fecha de modificación cerrada, jugador no elegible, cupo agotado, persona duplicada por disciplina, compra pendiente. **Aceptación:** después de retirar un jugador, cupo se actualiza y su compra no desaparece.

## ACCOUNT-04/05 — Mis compras y detalle

Mostrar compra agrupada por origen (inscripción/pase/tienda), fecha, importe, estado, qué se obtuvo y acción siguiente. Las compras invitadas se recuperan **mediante enlace privado**; no se exponen al solo digitar DNI. **PD-07:** decidir si las inscripciones también admiten compra como invitado.

## Criterios de calidad UX para estas páginas

- Formularios preservan el trabajo al navegar cuando es razonable; confirmar antes de descartar.
- Mostrar causas de bloqueos con texto de negocio (“Ya participa en fútbol de esta edición”), no solo 409.
- Estado de pago incierto exige opción de consultar/reintentar de forma segura, nunca perder inscripción.
- En móvil, etapas breves y progreso visible; CTA sticky solo si no tapa información.
- `Persona` se presenta por nombre/documento; `Usuario` solo cuando se gestiona cuenta.
