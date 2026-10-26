# Plan Modular por Fases: Rediseño Destructivo Salesianos FEST

**Estado:** plan de ejecución.  
**Regla central:** cada fase ejecuta primero un **SDD Explore sin CodeGraph**, luego un **SDD Apply**, y termina con un **SDD Explore de validación contractual usando CodeGraph**.  
**Referencia técnica:** `INFORME_SDD_EXPLORACION_REDISENO_SALESIANOS_FEST.md`.  
**Referencia de negocio:** `ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md`.

---

## Reglas que aplican a todas las fases

- [ ] Leer todos los contratos aplicables en `contract/` antes de explorar y antes de aplicar.
- [ ] No usar CodeGraph durante ningún SDD Explore de este rediseño.
- [ ] Al cerrar cada Apply, ejecutar un Explore de validación que use CodeGraph para contrastar los cambios reales contra `contract/`.
- [ ] No marcar una fase como completa hasta que la validación contractual posterior confirme la estructura, flujos, dependencias y límites de responsabilidad.
- [ ] No escribir código durante el Explore; registrar evidencia, alcance y riesgos.
- [ ] Definir raíces permitidas de edición para cada Apply antes de tocar archivos.
- [ ] Mantener controller thin, flujo atómico, presenter puro y mensajes públicos seguros.
- [ ] No crear compatibilidad, adaptadores legacy, dual-write ni migración de datos heredados.
- [ ] Ejecutar pruebas del bloque y revisar `git diff --check` antes de cerrar el Apply.
- [ ] Guardar artifacts SDD y progreso de apply en Engram.

## Convención por fase

### A. SDD Explore

- [ ] Leer `contract/` y la sección correspondiente de la especificación.
- [ ] Inspeccionar directamente solo los archivos implicados, sin CodeGraph.
- [ ] Actualizar inventario: eliminar, crear, modificar y conservar.
- [ ] Enumerar constraints, transacciones, endpoints, schemas, frontend y pruebas.
- [ ] Marcar decisiones pendientes que bloqueen ese bloque.

### B. SDD Apply

- [ ] Releer los contratos antes de editar.
- [ ] Aplicar exclusivamente el bloque aprobado y sus pruebas.
- [ ] No adelantar modelos ni campos de una fase futura sin necesidad validada.
- [ ] Verificar migraciones, DI, routers, schemas, frontend y tests afectados.
- [ ] Persistir el resultado y los comandos de verificación.

### C. SDD Explore de validación contractual

- [ ] Leer nuevamente `contract/` y el artifact del Explore inicial de la fase.
- [ ] Usar CodeGraph para inspeccionar los símbolos, imports, rutas y call paths realmente modificados.
- [ ] Contrastar el árbol real, responsabilidades de capas, schemas, DI, controllers, presenters y pruebas contra los contratos.
- [ ] Registrar incumplimientos por ruta/línea y corregirlos mediante un Apply correctivo antes de cerrar la fase.

---

## Fase 0: Contrato de mensajes públicos

**Objetivo:** cerrar el contrato HTTP antes de crear APIs nuevas.

### Explore

- [x] Auditar `api-wrapper-presenter-contract.md`, `django-app-architecture-contract.md` y `PLAN_REFACTORIZACION.md`.
- [x] Confirmar que los mensajes de error actuales pueden filtrar UUIDs desde `HttpError.message` y excepciones de dominio.
- [x] Definir ownership: controller para éxito fijo; handler global para error público por código.

### Apply

- [x] Añadir contrato de mensajes públicos y categorías de error.
- [x] Prohibir UUIDs, IDs internos, SQL, trazas, paths, secretos y texto crudo de excepciones en respuestas.
- [x] Definir jerarquía de excepción tipada, por ejemplo `HttpError -> NotFoundError -> CompraNotFoundError`.
- [ ] Aplicar el contrato al código de `core/exceptions.py` y excepciones existentes en una fase de código específica.

**Criterio de salida:** los tres contratos expresan la misma regla y ningún bloque nuevo puede inventar mensajes o retornar errores manuales.

---

## Fase 1: Corte destructivo y cimientos de módulos

**Objetivo:** dejar un entorno limpio y crear los límites de `eventos` y `salesianos_fest`.

**Estado:** completada el 2026-10-17. `pagos` queda deshabilitado hasta la Fase 4 porque sus modelos todavía tenían claves foráneas directas hacia el módulo eliminado.

### Explore

- [x] Localizar el comando real `reset dev`, su base de datos objetivo y sus efectos exactos.
- [x] Confirmar qué migraciones, seeds, routers, `INSTALLED_APPS` y DI deben eliminarse con `inscripciones`.
- [x] Delimitar el módulo mínimo `eventos` y el scaffold vacío de `salesianos_fest`.

### Apply

- [x] Ejecutar el reset destructivo aprobado sobre desarrollo, nunca sobre un entorno no confirmado.
- [x] Eliminar módulo, migraciones, seeds, rutas, DI, admin y tests de `inscripciones`.
- [x] Crear scaffolds contractuales de `eventos` y `salesianos_fest` sin adelantar modelos de Fase 2.
- [x] Registrar apps, DI y API mínimos necesarios.
- [x] Comprobar que el backend arranca con una base de datos limpia.
- [x] Deshabilitar temporalmente `pagos`: sus FKs hacia `inscripciones` impedían el arranque; se rediseña y rehabilita en Fase 4.
- [x] Ejecutar Explore de validación contractual con CodeGraph. El scaffold cumple; las referencias heredadas quedan aisladas dentro de `pagos` deshabilitado para su eliminación en Fase 4.

**Criterio de salida:** no existe código activo que importe `modules.inscripciones`; `eventos` no contiene lógica deportiva; `salesianos_fest` arranca vacío y registrado.

---

## Fase 2: Catálogos comerciales y deportivos

**Objetivo:** modelar datos que no dependen todavía de inscripciones ni pagos.

**Estado:** completada y validada contractualmente con CodeGraph el 2026-10-18.

### Explore

- [x] Revisar reglas de `Disciplina`, `Promocion`, `Categoria`, `Paquete`, `PaqueteDisciplina`, `PaquetePrecio` y `PaqueteBeneficio`.
- [x] Resolver el alcance de categorías por evento; diferir las disciplinas elegibles de Dúo/Trío sin inventarlas.
- [x] Especificar seeds de las ocho ofertas sin duplicar precio total de equipo.

### Apply

- [x] Crear modelos, choices, constraints, índices, admin, schemas, presenters, selectors y endpoints de catálogo.
- [x] Impedir solapes de precios y duplicados paquete-disciplina/paquete-beneficio.
- [x] Crear seeds únicamente con datos de negocio confirmados.
- [x] Diferir frontend de consulta: no era necesario para validar el catálogo backend de esta fase.
- [x] Añadir pruebas de catálogo, restricciones y mensajes públicos.
- [x] Generar y aplicar migraciones limpias; validar el Apply con CodeGraph y ocho tests de integración.

**Criterio de salida:** se pueden consultar las ofertas y sus precios vigentes; ninguna inscripción, compra ni pago existe aún.

---

## Fase 3: Inscripción deportiva, equipos y R11

**Objetivo:** crear el dominio deportivo sin derechos económicos.

### Explore

- [ ] Resolver política de fusión y máximos deportivos necesarios para este bloque.
- [ ] Diseñar `Inscripcion`, `Equipo`, `InscripcionPersona` y `Participacion` con constraints PostgreSQL.
- [ ] Validar la estrategia de constraint parcial para R11 bajo concurrencia.

### Apply

- [ ] Crear inscripción con paquete, promoción, equipos y personas registradas.
- [ ] Separar estado deportivo de cualquier estado de pago.
- [ ] Implementar R11: una persona no juega dos veces la misma disciplina dentro del evento.
- [ ] Permitir varias participaciones de la misma persona en disciplinas distintas de una inscripción.
- [ ] Reemplazar el wizard y detalle frontend exclusivamente para este dominio deportivo.
- [ ] Cubrir creación, edición deportiva y conflictos R11 mediante tests.

**Criterio de salida:** una inscripción puede registrar roster y equipos, pero no posee compra, cupo pagado, fiesta ni QR.

---

## Fase 4: Frontera genérica de pagos y compras

**Objetivo:** desacoplar Izipay de inscripción y modelar la obligación comercial.

### Explore

- [ ] Definir cardinalidad final `Compra <-> OrdenPago` ante vencimiento/reemisión.
- [ ] Definir fijación de precio y política de pago manual/reembolso si entran en alcance.
- [ ] Auditar todos los consumidores de `IzipayTransaccion.inscripcion` y del SDK frontend.

### Apply

- [ ] Crear `pagos.OrdenPago` y adaptar `TransaccionPago`/Izipay para referenciarla.
- [ ] Crear `Compra` INICIAL/AMPLIACION con snapshot de cantidad, precio unitario y total.
- [ ] Crear una compra inicial por inscripción y ampliaciones sin mínimo inicial.
- [ ] Reemplazar los endpoints Izipay basados en `inscripcion_id` por endpoints basados en una orden de pago autorizada.
- [ ] Reemplazar el servicio frontend de pagos para operar con la orden, sin monto ni secreto de cliente.
- [ ] Probar fallo, éxito, callback duplicado y reintento sin crear compras o derechos duplicados.

**Criterio de salida:** una compra pendiente puede cobrarse mediante una orden genérica; el pago no confirma el estado deportivo.

---

## Fase 5: Asignación de cupos, beneficios y acreditación

**Objetivo:** entregar derechos pagados y controlar acceso efectivo por evento.

### Explore

- [ ] Resolver estados canónicos de `AcreditacionEvento`, precedencia y alcance de `acceso_box`.
- [ ] Confirmar si box/cerveza requieren registro de entrega por inscripción.
- [ ] Diseñar locks y constraints para último cupo y QR de uso único.

### Apply

- [ ] Crear `AsignacionCupo` solo al confirmar un pago y sin filas vacías.
- [ ] Implementar saldo por inscripción y ampliaciones.
- [ ] Crear y recalcular `AcreditacionEvento` desde todos sus orígenes activos.
- [ ] Implementar override administrativo auditable de fiesta.
- [ ] Crear `ControlAcceso` y flujo QR atómico.
- [ ] Implementar frontend de compras, saldo, acreditación y acciones administrativas aprobadas.
- [ ] Ejecutar T02-T16 y pruebas PostgreSQL concurrentes T14/T15.

**Criterio de salida:** un cupo no se transfiere entre inscripciones y un QR no permite doble ingreso concurrente.

---

## Fase 6: Consentimientos y ajuste final de Persona

**Objetivo:** mover aceptación al vínculo correcto y retirar flags globales.

### Explore

- [ ] Resolver quién acepta por cada participante, qué evidencia legal se almacena y si el consentimiento es versionable.
- [ ] Identificar todas las referencias a `Persona.acepto_bases`, `acepto_aptitud_fisica` y `acepto_imagen`.

### Apply

- [ ] Crear `AceptacionInscripcion` por `InscripcionPersona` con versión, fecha, actor y medio aprobados.
- [ ] Integrar consentimiento en el flujo y frontend de inscripción/participantes.
- [ ] Eliminar flags de aceptación de `Persona`, sus schemas, presenters, endpoints y pruebas antiguas.
- [ ] No migrar los booleans heredados: no prueban inscripción, versión, fecha ni autor.
- [ ] Ejecutar T22 y pruebas de autorización de quien declara.

**Criterio de salida:** `Persona` conserva identidad; cada aceptación pertenece a una persona dentro de una inscripción y es auditable.

---

## Fase 7: Reemplazo total de experiencia frontend y API heredada

**Objetivo:** retirar cualquier ruta/pantalla/cliente que represente el modelo anterior.

### Explore

- [ ] Inventariar imports, enlaces de landing/sidebar/dashboard y dependencias de cache de `/inscripciones/*`.
- [ ] Confirmar diseño de páginas para catálogo, creación, detalle, compra, pago, roster, acreditación y administración.

### Apply

- [ ] Eliminar `features/inscripciones` heredado y sus rutas/pantallas asociadas.
- [ ] Implementar feature `salesianos-fest` con schemas Zod espejo de contratos backend.
- [ ] Reemplazar enlaces de landing, sidebar y dashboard.
- [ ] Retirar servicios que exponen `inscripcion_id` o campos de consentimiento global.
- [ ] Garantizar que mensajes de éxito/error vienen del contrato API, no de IDs ni strings técnicos construidos en UI.

**Criterio de salida:** el frontend no contiene solicitudes a `/inscripciones/*` ni referencias al dominio eliminado.

---

## Fase 8: Seeds, pruebas integrales y corte verificable

**Objetivo:** demostrar que el sistema nuevo cumple el negocio de extremo a extremo.

### Explore

- [ ] Revisar cobertura real de T01-T23, pruebas contractuales, e2e y concurrencia.
- [ ] Confirmar datos necesarios para seeds y roles administrativos.

### Apply

- [ ] Crear seeds finales de evento, promociones, categorías, disciplinas, ofertas, precios y beneficios confirmados.
- [ ] Ejecutar T01-T23, pruebas HTTP async, tests de mensajes seguros y PostgreSQL concurrente.
- [ ] Verificar Izipay sandbox y conciliación sin secretos en logs o respuestas.
- [ ] Confirmar que no quedan imports, rutas, tablas ni migraciones del dominio eliminado.
- [ ] Documentar comando de bootstrap de desarrollo posterior al reset.

**Criterio de salida:** sistema nuevo reproducible desde base limpia, con pruebas ejecutadas y sin dependencia funcional de `inscripciones`.

---

## Orden obligatorio

```text
Fase 0 -> Fase 1 -> Fase 2 -> Fase 3 -> Fase 4 -> Fase 5 -> Fase 6 -> Fase 7 -> Fase 8
```

No se inicia un Apply de la siguiente fase mientras no estén completos el Explore, los pendientes aplicables, el diff y las verificaciones de la fase actual.
