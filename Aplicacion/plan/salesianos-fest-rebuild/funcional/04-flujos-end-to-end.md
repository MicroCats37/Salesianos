# Funcional 04 — Flujos de extremo a extremo

Cada flujo describe **intención → precondiciones → acción → resultado → error/recuperación**. Endpoint y URL exactos se concretan en los contratos posteriores.

## FL-01 — Cambiar edición y consultar catálogo

1. Visitante entra a Salesianos FEST; sistema indica edición publicada y módulos habilitados.
2. Consulta disciplinas, paquetes, entradas y productos solo si existen y están publicados para esa edición.
3. Si no existe información, mostrar estado vacío o no publicado; **no inventar un catálogo estático con precios ficticios**.
4. Se puede acceder al histórico público de ediciones si se decide exponerlo (propuesta, no requisito confirmado).

## FL-02 — Resolver persona por documento

1. Formulario solicita tipo/documento; consultar BD local por coincidencia exacta.
2. Si no existe, consultar RENIEC mediante servicio ya disponible; indicar error si falla o el documento no existe.
3. Confirmado el uso de la persona (inscripción/compra/asignación), persistir `Persona` sin duplicar.
4. Si el actor no es titular, no otorgar por ese solo dato acceso a cuentas/compras ajenas.

## FL-03 — Inscribir equipo y comprar cupos iniciales

1. Responsable autenticado selecciona paquete, edición, promoción y disciplinas permitidas.
2. Se muestran mínimo/condiciones y cotización validada en backend.
3. Completa equipos y confirma inscripción; backend crea inscripción, compra/orden pendientes.
4. Izipay muestra checkout; si se cierra el modal, la compra permanece pendiente.
5. Confirmación confiable de pago habilita cupos; responsable ve cupos adquiridos/asignados/disponibles.
6. Puede añadir personas al pool y asignarlas a equipos según elegibilidad; no asignar cupos no pagados.
7. Ante intento duplicado o pago tardío, no repetir creación/asignación.

## FL-04 — Ampliar cupos de inscripción

1. Responsable abre detalle de inscripción y consulta saldo; elige cantidad adicional.
2. Se valida límite/fecha/precio; compra independiente vinculada a **la misma inscripción**.
3. Al pago, se agregan cupos al pool una sola vez.
4. Beneficios por cupo se conceden conforme a regla; los beneficios fijos iniciales no se duplican automáticamente.

## FL-05 — Gestionar plantilla

1. Responsable abre inscripción → pool → equipos.
2. Agrega Persona existente o la resuelve por documento; consulta elegibilidad antes de asignar.
3. Asigna persona y cupo disponible, con transacción de servidor; muestra resultado y saldo actualizado.
4. Retira o mueve participante: libera/reasigna cupo de esa inscripción según reglas, sin generar dinero nuevo.
5. Administrador ve causas concretas de equipo incompleto/no elegible.

## FL-06 — Comprar pase sin cuenta

1. Visitante elige pase, cantidad, identifica comprador con DNI y deja correo.
2. Compra y orden independientes del deporte; no se crea obligatoriamente `Usuario`.
3. Tras pago verificado, el lote habilita entradas pendientes de asignación.
4. Comprador recibe enlace privado de recuperación/gestión cuando el servicio de correo esté configurado; email fallido no deshace pago.
5. Asigna pases a Personas mediante documento; se respeta límite/duplicidad; `PD-02` define revocación y reasignación.

## FL-07 — Otorgar cortesía administrativa

1. Administrador localiza Persona y edición, selecciona entrada permitida.
2. Indica motivo; backend registra derecho gratuito con auditoría.
3. Nunca crea orden o transacción de pago ficticia.
4. Puede invalidar la cortesía conforme a política; deja historial.

## FL-08 — Comprar producto de tienda

1. Visitante abre categoría y producto, explora galería; elige cantidad.
2. Se crea pedido de marketplace con detalle/precio snapshot y compra/orden de pago.
3. Backend impide venta sin stock con estrategia anti-sobreventa acordada.
4. Pago confirmado → pedido pagado, inventario actualizado/reserva confirmada según política.
5. Si requiere recogida, un operador entrega usando ticket y registro de consumo; «pagado» y «entregado» son distintos.

## FL-09 — Ajuste/consumo de stock administrativo

1. Administrador busca producto, selecciona entrada/salida/ajuste y cantidad.
2. Indica motivo y confirma; backend valida disponibilidad y registra movimiento con actor.
3. El stock cambia y se consulta la bitácora; no hay compra/pago en una salida sin venta.

## FL-10 — Validar entrada o entrega

1. Operador entra a pantalla especializada de **pases** o **marketplace**.
2. Escanea QR o ingresa código; el servicio común identifica credencial y consulta el derecho propietario.
3. Pantalla muestra tipo, titular, pendiente/consumido/bloqueado, cantidad y motivo si no se permite.
4. Operador **confirma** ingreso o entrega; backend vuelve a validar de forma atómica e idempotente.
5. Relectura posterior de ticket consumido no permite doble uso; quedan actor, hora y resultado.

## FL-11 — Administrar competencia y encuentros

1. Administrador selecciona edición, disciplina/categoría y competencia.
2. Crea/edita rondas y selecciona equipos elegibles, según reglas.
3. Configura encuentros, horarios y enlaces/bye donde corresponde.
4. Registra resultado y ganador; previsualiza avance y confirma.
5. Ante corrección tardía, muestra impacto y exige confirmación/motivo sin cascada oculta.
6. Lista, agenda y bracket comparten una sola fuente de datos operativa.

## FL-12 — Investigar incidencia de pago

1. Administrador filtra por **estado entendible**: pendiente, confirmado, en verificación, necesita atención, etc.
2. Abre detalle de compra (producto/origen/persona), orden e intentos **en secciones separadas**.
3. Ve qué derecho se habilitó o qué operación necesita revisión.
4. Las acciones financieras sensibles requieren permiso administrativo, motivo y validación por backend.
5. No mostrar «liquidación» como etiqueta de cara a operador; usar «Beneficio habilitado», «Cupos disponibles», «Entrada pendiente de asignación».

## Matriz de recuperación común

| Situación | Comportamiento |
|---|---|
| Browser cierra modal | Compra persiste y se puede recuperar |
| Checkout reabierto | Consultar intento y orden; no crear compra duplicada |
| Webhook repetido | Idempotencia de pago y de activación |
| Correo no enviado | Compra pagada persiste; notificación reintentable |
| Reserva de stock vence | Liberar conforme a política elegida; sin venta ficticia |
| Sesión caducada | Solicitar login o vínculo seguro, conservar intención cuando sea posible |
| No hay edición activa | Informar claramente; no atribuir operaciones a otra edición |
| Ticket ya utilizado | Rechazar nuevo consumo y mostrar registro previo si autorizado |
