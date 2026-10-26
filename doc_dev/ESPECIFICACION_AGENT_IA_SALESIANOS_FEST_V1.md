# Especificación técnico-funcional para agente de IA — Rediseño Salesianos Fest

**Estado:** propuesta consolidada para revisión e implementación incremental; NO interpretar los puntos pendientes como decisiones aprobadas.  
**Fecha:** 17 de octubre de 2026.  
**Destinatario:** agente de IA encargado de explorar el repositorio y ejecutar el rediseño.  
**Referencia:** `INSCRIPCIONES_REPLANTEAMIENTO_MAPA(1).md` (auditoría del sistema anterior). Las reglas nuevas acordadas en conversación prevalecen sobre la implementación heredada.

## 0. Instrucciones obligatorias para el agente ejecutor

1. **Antes de tocar código, localizar y LEER la carpeta `contract` real del repositorio** y las instrucciones adicionales que allí existan (contratos arquitectónicos, nombres, servicios, pruebas, conventions, entrypoints). No se suministró su contenido en esta conversación: **no inventar rutas, convenciones ni contratos**. Si `contract` contradice este documento, presentar el conflicto antes de implementar; no sustituir silenciosamente una regla del negocio.
2. Este trabajo es **rediseño desde cero del dominio de inscripciones**, no una migración conceptual uno-a-uno de tablas viejas. Usar la auditoría anterior para rescatar campos, integraciones y casos, no para copiar relaciones. La estrategia de datos históricos y corte de despliegue debe acordarse por separado.
3. Crear diseño y código por bloques revisables. **No generar todos los modelos/migraciones/endpoints en una sola pasada sin revisar primero el ER y casos de prueba.**
4. Respetar `BaseModel` existente: en los cuadros de este informe **se omiten `id`, `created_at`, `updated_at`** y cualquier otro campo heredado. No duplicarlos.
5. Entregar primero propuesta de modelos con `ForeignKey`, `OneToOne`, `UniqueConstraint`, `CheckConstraint`, índices, `on_delete`, transiciones y casos de prueba. Implementar solo tras aprobación.
6. Separar **hechos acordados**, **recomendaciones técnicas** y **puntos no confirmados**. No convertir una sugerencia en regla irrevocable.
7. Mantener operaciones sensibles en `transaction.atomic()`, idempotencia de callbacks y control de concurrencia al asignar/liberar cupos. Usar el patrón de arquitectura real documentado en `contract`.
8. Integrar historial/auditoría (`simple_history` se utiliza hoy), sin asumir que por sí solo sustituye registros de transiciones económicas y de consentimientos.

## 1. Alcance de arquitectura

La plataforma tiene un módulo **`eventos` genérico mínimo** y un módulo de negocio **`salesianos_fest` específico**. El primero no debe importar modelos ni servicios deportivos. El frontend puede tener shell/autenticación compartidos y flujos/páginas específicos del módulo; no crear un CMS ni motor de plugins ahora. Futuras ediciones reutilizan el mismo módulo deportivo con datos aislados por `Evento`; conferencias u otros formatos pueden disponer de módulos propios.

`usuarios` contiene `Persona` y su vinculación a identidad/autenticación. `pagos` abstrae el cobro y proveedores. `salesianos_fest` contiene catálogo deportivo, paquetes, inscripciones, equipos, participantes, compra de cupos, beneficios y acreditación correspondiente a ese evento. La ubicación definitiva de `AcreditacionEvento` (núcleo o módulo del evento) requiere acordarse por su alcance; **no convertirla automáticamente en abstracción para todos los eventos**.

## 2. Invariantes de negocio confirmadas

1. Hay cuatro packs (Reencuentro, Pichanga, Dúo, Trío) y venta individual por disciplina. **Una sola tabla `Paquete`** representa las ocho ofertas, con `tipo=PACK|DISCIPLINA`.
2. `PaqueteDisciplina` sirve tanto a `FIJO` (disciplinas predeterminadas) como a `ELEGIBLE` (conjunto de opciones permitidas, con cantidad a seleccionar). La selección efectiva se materializa en los equipos de la inscripción.
3. Cantidad mínima de compra inicial: Reencuentro 10, Pichanga 10, Dúo 15, Trío 20, fútbol por disciplina 7, vóley 6, básquet 5. **Mínimo comercial ≠ máximo deportivo ≠ número de personas distintas registradas en un momento**.
4. Tarifas conocidas: **PREVENTA y REGULAR**, por persona; cada compra utiliza la vigente y congela `precio_unitario` y `total`. La ampliación **no repite el mínimo inicial**.
5. El comprador puede seleccionar paquete/equipos, solicitar 10 cupos, registrar 7 personas y pagar los 10. Puede completar los 3 faltantes posteriormente dentro del plazo de modificación. No generar asignaciones ficticias para los cupos no asignados.
6. `Compra` pendiente representa cupos contratados, **no pagados**. Las personas pueden quedar registradas antes del cobro dentro de la cantidad contratada; solo al confirmar pago se crean/formalizan `AsignacionCupo` pagadas para personas elegibles. Las personas no asignadas quedan sin derechos pagados.
7. Una inscripción puede tener una compra inicial y N compras de ampliación. Cupos y saldo **pertenecen siempre a la inscripción**. Nunca transferir saldo entre inscripciones, aunque tengan igual responsable o participante.
8. La misma persona puede jugar en varias disciplinas dentro de una inscripción y consume **un solo cupo comercial** de esa inscripción. No puede jugar dos veces en la **misma disciplina del mismo evento**, aunque sea en inscripciones diferentes (regla R11).
9. Si aparece en dos inscripciones de compradores distintos, cada inscripción necesita su propio cupo pagado. No regalar descuentos, traspasos ni compensaciones entre compradores.
10. Los cupos de packs Dúo/Trío son para **jugadores registrados**, no invitados exclusivamente de fiesta. Cada cupo nuevo de pack con fiesta concede pase individual a fiesta. Packs sin fiesta no lo conceden.
11. Box y caja de cerveza son **beneficios colectivos** de la inscripción, no repetidos por persona ni ampliación. No confundir derecho de box grupal con permiso individual de entrada a zona box.
12. Un único registro de `AcreditacionEvento` por `(evento, persona)` representa **permisos efectivos**; puede existir más de un origen de compra. Un solo acceso/QR efectivo a fiesta por persona y evento, aun con dos compras que la cubran.
13. Admin puede permitir fiesta a quien compró solamente deporte, o bloquear a quien sí pagó. Ese override **no debe borrarse en la siguiente sincronización**. Registrar autor, motivo y momento de la acción de forma auditable.
14. Si reemplazan a alguien antes del cierre, se retiran sus participaciones de la inscripción, se libera la asignación histórica y se recalculan sus permisos por **todos sus orígenes activos**, no solo por la inscripción que cambió. No se devuelve ni cambia el precio pagado por la liberación.
15. Las categorías son generales del campeonato (Junior/Senior/Master/Super Master), **no dependen directamente de `Disciplina`**. Se resuelven automáticamente por año de promoción principal. Fusiones se validan por servicio, sin tabla independiente de reglas por ahora.
16. `Inscripcion.promocion` es la promoción principal, `fusion_promocion` es opcional. `Equipo.promocion` es FK **opcional reservada para posible uso futuro**, **no utilizada por el flujo actual**: actualmente todos los equipos heredan la promoción de inscripción.
17. `Persona` no requiere `colegio` dentro de `Promocion`: el dominio es Salesianos; `Promocion.anio` único.
18. Aceptaciones de bases, aptitud física y uso de imagen se registran **por persona y por inscripción**, no como tres flags globales permanentes de `Persona`. Hay que comprobar quién otorga el consentimiento; el responsable no puede fingir aceptación de un tercero.
19. Estados deportivos de inscripción, pagos y permisos/participaciones deben ser independientes.

## 3. Datos comerciales iniciales acordados

| Oferta | Tipo | Modo | N.º disciplinas | Compra mínima | Preventa/persona | Regular/persona | Beneficio fiesta |
|---|---|---|---:|---:|---:|---:|---|
| Reencuentro + Fiesta | PACK | ELEGIBLE | 1 | 10 | S/40 | S/50 | Sí |
| Pichanga + Fiesta | PACK | FIJO | 1 | 10 | S/45 | S/55 | Sí |
| Dúo + Fiesta Box | PACK | ELEGIBLE | 2 | 15 | S/60 | S/70 | Sí + box + caja |
| Trío + Fiesta Box | PACK | ELEGIBLE | 3 | 20 | S/60 | S/70 | Sí + box + caja |
| Fútbol 7 masculino | DISCIPLINA | FIJO | 1 | 7 | S/40 | S/50 | No |
| Fútbol 7 femenino | DISCIPLINA | FIJO | 1 | 7 | S/40 | S/50 | No |
| Vóley mixto | DISCIPLINA | FIJO | 1 | 6 | S/40 | S/50 | No |
| Básquet masculino | DISCIPLINA | FIJO | 1 | 5 | S/40 | S/50 | No |

Reencuentro permite elegir entre Fútbol 7 femenino, Vóley mixto y Básquet masculino; Pichanga fija Fútbol 7 masculino. Para Dúo/Trío, verificar las disciplinas concretas elegibles en los folletos/catálogo antes de crear seeds. En Dúo/Trío los 15/20 son mínimos comerciales, **no máximos de plantilla**. Los precios de equipo en folleto son el producto del mínimo por el precio por persona; no mantener una segunda tarifa total duplicada si se confirma esta regla para toda oferta.

Categorías mostradas: Junior 2012–2025; Senior 1998–2011; Master 1985–1997; Super Master 1970–1984. El organizador puede reconfigurarlas. En una edición siguiente no modificar clasificaciones históricas.

## 4. Catálogo de tablas propuesto — omitir campos de BaseModel

**Convención:** nombres orientativos; respetar `contract` en nomenclatura final. Tipos `FK` son relaciones conceptuales Django, no SQL definitivo. Marcar las notas **[REVISAR]** antes de codificar.

### 4.1 Módulo común `eventos`

**Evento:** `nombre: CharField(200)`, `fecha_inicio: DateField`, `fecha_fin: DateField`, `esta_activo: BooleanField`. Mínimo compartido, sin lógica deportiva.

### 4.2 Módulo `usuarios`

**Persona:** `nombres`, `apellidos`, `tipo_documento`, `numero_documento`, `genero`, `telefono?`, `whatsapp?`, `contacto_emergencia_nombre?`, `contacto_emergencia_telefono?`, `aseguradora_nombre?`, `aseguradora_numero_poliza?`. Identidad única `(tipo_documento, numero_documento)`. Tomar longitudes y choices del repositorio/contratos. Los datos de seguro podrían necesitar snapshot por inscripción si cambian entre ediciones **[REVISAR]**. **Usuario**: vinculación con `Persona` según el modelo de autenticación existente; no reimplementar login.

### 4.3 Catálogos `salesianos_fest`

| Tabla | Campos específicos | Restricciones / notas |
|---|---|---|
| **Disciplina** | `nombre`, `sigla`, `modalidad: M/F/X`, `min_jugadores?`, `max_jugadores?`, `esta_activa` | `sigla` única; los mínimos/máximos son **por equipo**, no por deporte global. Sin `EventoDisciplina`. |
| **Promocion** | `anio`, `nombre`, `activa` | `anio` único, sin `colegio`. |
| **Categoria** | `nombre`, `promocion_desde`, `promocion_hasta`, `esta_activa`, **`evento?` [REVISAR]** | Sin FK a disciplina. Debe permitir configurar rangos distintos por edición sin reescribir historial. Acordar si `evento` FK directa o catálogo versionado por edición **antes de migraciones**. Rango desde ≤ hasta; no solapes activos por ámbito. |

### 4.4 Ofertas y precios

| Tabla | Campos específicos | Restricciones / notas |
|---|---|---|
| **Paquete** | `evento: FK(Evento)`, `nombre`, `descripcion?`, `tipo: PACK/DISCIPLINA`, `modo_disciplinas: FIJO/ELEGIBLE`, `cantidad_disciplinas`, `minimo_compra_inicial`, `activo` | Una oferta por evento; paquete elegido no se modifica tras confirmar la selección. No incluir `precio_preventa` y `precio_regular` duplicados. |
| **PaqueteDisciplina** | `paquete: FK(Paquete)`, `disciplina: FK(Disciplina)` | Única `(paquete, disciplina)`; misma tabla para opciones FIJO/ELEGIBLE. Podría usar clave compuesta si `contract` y la implementación lo permiten. |
| **PaquetePrecio** | `paquete: FK(Paquete)`, `etapa: PREVENTA/REGULAR`, `precio_unitario: Decimal(10,2)`, `vigente_desde`, `vigente_hasta?`, `activo` | Sin periodos aplicables solapados. Compra conserva snapshot unitario; aclarar precio al crear compra vs al iniciar pago. |
| **PaqueteBeneficio** | `paquete: FK(Paquete)`, `tipo: FIESTA/BOX/CERVEZA`, `cantidad: PositiveInteger`, `alcance: INDIVIDUAL/GRUPAL`, `modo_calculo: POR_CUPO/FIJO_INICIAL` | Catálogo, **no** saldo ni acreditación. Fiesta: `1 POR_CUPO INDIVIDUAL`; box/caja: `1 FIJO_INICIAL GRUPAL` en Dúo/Trío. Única configuración por `(paquete, tipo)` si un tipo no admite varias variantes. |

### 4.5 Inscripción y equipos

| Tabla | Campos específicos | Restricciones / notas |
|---|---|---|
| **Inscripcion** | `evento: FK(Evento)`, `responsable: FK(Persona)`, `paquete: FK(Paquete)`, `promocion: FK(Promocion)`, `fusion_promocion?: FK(Promocion)`, `delegado?: FK(Persona)`, `estado`, `observacion?` | Una inscripción puede tener varias compras; `estado` exclusivamente deportivo/administrativo, sin `PAGADA`. Paquete pertenece al mismo evento. Solo una fusión adicional en el modelo pactado. |
| **Equipo** | `inscripcion: FK(Inscripcion)`, `disciplina: FK(Disciplina)`, `categoria?: FK(Categoria)`, `promocion?: FK(Promocion)`, `nombre`, `estado` | `promocion` opcional **no usada ahora**; categoría calculada desde `Inscripcion.promocion` principal. Disciplina debe pertenecer al paquete. Verificar si existe exactamente uno por disciplina e inscripción; propuesta inicial: sí. |
| **InscripcionPersona** | `inscripcion: FK(Inscripcion)`, `persona: FK(Persona)`, `estado: ACTIVO/RETIRADO` | Único `(inscripcion, persona)`, reutilizable en varios equipos de esa inscripción. Persona registrada ≠ cupo pagado. |
| **Participacion** | `inscripcion_persona: FK(InscripcionPersona)`, `equipo: FK(Equipo)`, `rol: JUGADOR/CAPITAN/DELEGADO`, `talla_camiseta?`, `notas?`, `estado: ACTIVA/RETIRADA` | Para garantizar R11 en DB bajo concurrencia, **considerar también** `evento: FK(Evento)`, `disciplina: FK(Disciplina)` y `persona: FK(Persona)` redundantes pero verificados contra equipo/inscripción. Índice único parcial activos `(evento, disciplina, persona)`. Si el agente propone alternativa DB íntegra sin redundancia, explicar y probarla. |

**Nota sobre delegado:** una FK opcional en `Inscripcion` es suficiente para 1 delegado vigente, siempre que cumpla elegibilidad. No crear `InscripcionDelegado` sin necesidad adicional de historial independiente.

### 4.6 Compra y pagos

| Tabla | Campos específicos | Restricciones / notas |
|---|---|---|
| **Compra** (`salesianos_fest`) | `inscripcion: FK(Inscripcion)`, `tipo: INICIAL/AMPLIACION`, `cantidad: PositiveInteger`, `precio_unitario: Decimal(10,2)`, `total: Decimal(10,2)`, `estado: PENDIENTE/PAGADA/CANCELADA` , `orden_pago: OneToOne(OrdenPago)?` | Compra de un solo concepto, por ahora **sin `CompraDetalle`**. Mantener snapshot. Una compra inicial válida por inscripción y N ampliaciones. Resolver semántica de compras pendientes y canceladas. |
| **OrdenPago** (`pagos`) | `numero: CharField(unique)`, `monto_total: Decimal(10,2)`, `moneda: PEN`, `estado: PENDIENTE/PAGADA/CANCELADA`, `pagada_en?` | Agnóstica del negocio. La referencia desde Compra puede ser `OneToOne` si una compra se cobra con una sola orden reutilizada para N intentos; confirmar cardinalidad de reemisiones/cancelaciones. |
| **TransaccionPago** (`pagos`) | `orden_pago: FK(OrdenPago)`, `proveedor`, `transaction_id`, `order_number`, `amount`, `currency`, `status`, `response_code?`, `response_message?`, `metodo_pago?`, `metadata: JSONField` | Reutilizar estructura del `IzipayTransaccion` viejo cambiando referencia a `OrdenPago`, no a `Inscripcion`. Varias transacciones por orden. Única `(proveedor, transaction_id)` donde aplica. Confirmar con proveedor por canal autenticado, idempotencia y conciliación. |

**No introducir aún `CompraDetalle`**: ahora cada compra contiene N cupos homogéneos del paquete y un precio unitario. Si el usuario más adelante compra varios productos heterogéneos en un mismo pedido, esa funcionalidad requerirá `CompraDetalle` o líneas de pedido del módulo correspondiente. No acoplar la futura tienda a `salesianos_fest.Compra`.

### 4.7 Asignación comercial y acreditación

| Tabla | Campos específicos | Restricciones / notas |
|---|---|---|
| **AsignacionCupo** | `inscripcion: FK(Inscripcion)`, `compra: FK(Compra)`, `inscripcion_persona: FK(InscripcionPersona)`, `estado: ACTIVA/LIBERADA/REVOCADA`, `motivo?`, `liberada_en?` | **Se crea al confirmarse compra** para personas registradas y cubiertas; para personas añadidas después de pagar, al consumir saldo pagado disponible. No crear filas vacías. Origen compra e inscripción deben coincidir. Solo una asignación activa por `(inscripcion, persona)`; respetar cantidad pagada por compra bajo concurrencia. |
| **AcreditacionEvento** | `evento: FK(Evento)`, `persona: FK(Persona)`, `estado: PENDIENTE/ACTIVA/SUSPENDIDA/REVOCADA`, `acceso_fiesta: Boolean`, `acceso_box?: Boolean`, `autorizacion_fiesta: AUTOMATICA/AUTORIZADA/BLOQUEADA`, `habilitado: Boolean?`, `codigo_qr?: UUID unique`, `observacion?` | Única `(evento, persona)`. Permiso **efectivo**, no dueño del cupo. Evitar semánticas contradictorias entre `estado` y `habilitado` (elegir una representación canónica). Override admin prevalece ante recálculo automático. `acceso_box` solo si se controla acceso individual al área. |
| **ControlAcceso** | `acreditacion: FK(AcreditacionEvento)`, `fecha_hora`, `resultado: PERMITIDO/DENEGADO`, `punto_acceso?`, `operador?: FK(Usuario)` | Intentos y resultados de QR; un solo ingreso válido si acceso de uso único. Validaciones concurrentes atómicas. |

**Trazabilidad de fiesta con orígenes múltiples:** La acreditación global no debe guardar `inscripcion_id` único. Al resolver/revocar fiesta, consultar las `AsignacionCupo` activas y compras pagadas con `PaqueteBeneficio(FIESTA)` vinculadas al evento, además de overrides administrativos. Se puede mantener sin `EntradaOrigen` adicional si consultas, volumen y auditoría lo permiten; si se requiere snapshot de orígenes o distinguir revocaciones por fuente, justificar una tabla puente explícita. **No asumir que un booleano es evidencia suficiente del origen.**

**Beneficio colectivo efectivo [PENDIENTE]:** `PaqueteBeneficio` es configuración. Todavía falta decisión sobre registrar entrega/canje de box y caja de cerveza. Si el negocio requiere saber asignado/entregado/revocado por inscripción, proponer **una tabla `BeneficioInscripcion`** con `inscripcion`, `tipo`, `cantidad_otorgada`, `cantidad_entregada`, `estado`, `origen_compra?`, `motivo?`. Crear solo tras validar el control real; no confundirlo con acreditación individual.

### 4.8 Aceptaciones por persona e inscripción

**AceptacionInscripcion** (opción recomendada para trazabilidad): `inscripcion_persona: OneToOne(InscripcionPersona)`, `acepto_bases: Boolean`, `acepto_aptitud_fisica: Boolean`, `acepto_imagen: Boolean`, `fecha_aceptacion?`, `version_bases?`, `aceptado_por?: FK(Persona o Usuario)`, `medio?`. Es distinta de permisos de fiesta y compra. Definir legalmente quién puede otorgar consentimiento y si un mismo consentimiento puede actualizarse o debe mantenerse historial de versiones. Si se requiere aceptación repetida/versionada, **no usar OneToOne**, sino varias filas por documento/versión; someter a aprobación.

## 5. Reglas de estado y transiciones

- **Inscripcion:** borrador/recibida → en revisión → observada/validada/confirmada/rechazada/cancelada, según políticas de comité. Evitar transiciones arbitrarias. **Pendiente:** máquina exacta y roles autorizados.
- **Compra:** pendiente → pagada o cancelada. La compra pagada no cambia su precio por cambios posteriores. Reembolsos/parciales requieren decisión adicional.
- **TransaccionPago:** pendiente → éxito/fallido/cancelado; N intentos por orden, a lo sumo una **aplicación económica** de derechos por compra. Si varios intentos realmente cobran, abrir incidente de conciliación/reembolso, no duplicar cupos.
- **InscripcionPersona/Participacion:** activo/retirado (sin eliminación destructiva de historial). Inscripción previa a pago permitida, **sin derechos pagados**.
- **AsignacionCupo:** activa solo cuando el cupo está pagado; liberada/revocada al retiro o ajuste. No hace falta `PENDIENTE` si la fila se crea exclusivamente después de pago. Un cupo sin persona se cuenta por saldo, no por fila nula.
- **AcreditacionEvento:** registrar estado efectivo y override admin separadamente. Precedencia recomendada `BLOQUEADA` > `AUTORIZADA` > derivación automática de derechos pagados. Determinar si suspensión general tiene prioridad universal. La sincronización no debe revertir un bloqueo explícito.
- **ControlAcceso:** ingreso no debe depender de tener una participación activa en *esa misma inscripción* si otra inscripción sigue financiando fiesta o existe autorización administrativa.

## 6. Flujos transaccionales de extremo a extremo

### F1 — Crear inscripción y compra inicial

1. Usuario autenticado elige `Evento`, `Paquete` vigente y N cupos ≥ mínimo inicial.
2. Selecciona las disciplinas requeridas según FIJO/ELEGIBLE; crea equipo(s). Todas las entidades deben pertenecer al mismo evento y paquete.
3. Selecciona `Promocion` principal y posible fusión validada mediante servicio. Equipo usa la promoción de inscripción; `Equipo.promocion` no está habilitada en la UI actual.
4. Se crea `Inscripcion` y `Compra(INICIAL, PENDIENTE, cantidad=N, precio_snapshot)`, con `OrdenPago` al iniciar el cobro (o creación, según contratos existentes). Registrar datos opcionales de 0..N personas únicas y sus `Participacion` dentro de disciplina.
5. Verificar cantidad de personas únicas ≤ cupos **contratados**; validar máximo deportivo por equipo aun en borrador. El mínimo deportivo se revisa para validación final, no impide borradores.
6. Antes de pago **no crear `AsignacionCupo` activa**; no activar fiesta ni otros derechos adquiridos.

### F2 — Confirmar pago Izipay

1. Recibir callback / verificación contra proveedor por mecanismo seguro y documentado.
2. Resolver transacción y orden, validar identidad, importe, moneda, resultado y no aplicación previa.
3. Dentro de transacción atómica y con bloqueo de registros necesarios: marcar intento, orden y compra pagados **una sola vez**.
4. Asignar cupos de la compra a personas registradas sin asignación activa, hasta capacidad de la compra. Los restantes quedan disponibles sin filas ficticias.
5. Crear/actualizar `AcreditacionEvento` de las personas efectivamente cubiertas. Aplicar beneficios individuales correspondientes al paquete (fiesta); conservar overrides administrativos.
6. El estado deportivo de la inscripción no cambia automáticamente a confirmado solo por pagar.

### F3 — Añadir persona después de pagar

1. Resolver `Inscripcion`, cupos contratados y pagados, y saldo libre **exclusivo de esa inscripción**.
2. Si hay cupo pagado libre, registrar/reutilizar `InscripcionPersona`, crear `Participacion` y `AsignacionCupo` con origen en una compra pagada de esa inscripción.
3. Actualizar acreditación efectiva. Para reuso de persona en otro deporte de la **misma** inscripción, crear participación adicional, no nuevo cupo.
4. Si no existe saldo, crear una ampliación `Compra(PENDIENTE)` antes de habilitar nuevos derechos. Definir en producto si datos de nuevos jugadores se capturan en borrador bajo esa ampliación o solo al pagar; nunca exceder cupos contratados.

### F4 — Compra de ampliación

1. Validar inscripción no cancelada, plazo de ventas, número de nuevos cupos > 0, paquete inmutable.
2. Calcular precio unitario de la tarifa vigente de **la fecha acordada para cotización**, congelándolo para esa compra. Mínimo inicial **no se aplica**.
3. Registrar `Compra(AMPLIACION)` y `OrdenPago`. El fracaso de un intento genera otra `TransaccionPago`, no necesariamente otra `Compra`.
4. Solo tras pago confirmado aumentar cupos pagados disponibles y habilitar asignaciones/personas correspondientes. Los derechos colectivos `FIJO_INICIAL` **no se duplican**.

### F5 — Reemplazar o retirar jugador

1. Validar permiso del responsable/admin y límite temporal de modificaciones.
2. Retirar participaciones de esa persona de **esa inscripción** (o, si retira solo una disciplina y mantiene otra, **conservar cupo**).
3. Si ya no juega en ninguna disciplina de esa inscripción: cambiar asignación activa a `LIBERADA`; mantener la compra pagada y cupo disponible de esa misma inscripción.
4. Recalcular `AcreditacionEvento` para la persona retirada considerando **todas** sus inscripciones con origen pagado; respetar overrides.
5. Permitir asignar el cupo liberado a otro jugador válido antes del cierre, registrando nueva asignación con el mismo origen comercial.

### F6 — Admin autoriza o bloquea fiesta

1. Verificar privilegios, motivo y actor.
2. Actualizar override explícito de acreditación (`AUTORIZADA`/`BLOQUEADA`) y calcular acceso efectivo.
3. Registrar historial/auditoría. No crear compra ficticia ni modificar cupos pagados.
4. Nueva compra o retirada no debe borrar la decisión del admin; solo una acción autorizada la cambia.

### F7 — Escaneo QR

1. Resolver acreditación de `(evento, persona)` a partir del token/QR no adivinable.
2. Validar evento, estado, `acceso_fiesta`, bloqueo, vigencia y condición de uso único.
3. Registrar resultado autorizado/denegado en `ControlAcceso` y evitar dos éxitos por concurrencia.

## 7. Fórmulas e integridad económica

Por cada inscripción:

- `contratados = SUM(compra.cantidad WHERE estado IN [PENDIENTE, PAGADA] y no cancelada)`.
- `pagados = SUM(compra.cantidad WHERE estado=PAGADA)`.
- `asignados_pagados = COUNT(AsignacionCupo WHERE estado=ACTIVA y compra pagada)`.
- `disponibles_pagados = pagados - asignados_pagados`.
- `registrados = COUNT(InscripcionPersona activas)`; incluir solo participantes activos al computar ocupación efectiva deportiva según la regla vigente.
- **Antes del pago inicial** `registrados ≤ contratados`; después, todo derecho de fiesta por compra requiere asignación pagada o override de admin. Evitar afirmar que `registrados ≤ pagados` en todos los estados, porque puede haber ampliación pendiente.
- Para cada compra pagada, `COUNT(asignaciones activas originadas en compra) ≤ compra.cantidad`. Una persona no puede tener dos asignaciones activas en la misma inscripción.
- El total de una compra = cantidad × precio unitario redondeado según moneda; servidor es fuente de verdad.

Reforzar reglas de consistencia entre `Inscripcion`, `Compra`, `AsignacionCupo`, `InscripcionPersona`, `Equipo` y `Participacion` con transacciones, constraints adecuados y, donde una FK no imponga igualdad entre cadenas, validaciones server-side. Priorizar pruebas de concurrencia con PostgreSQL real.

## 8. Pruebas de aceptación para el agente

| ID | Escenario | Resultado esperado |
|---|---|---|
| T01 | Reencuentro N=10, 7 personas antes de pago | 10 contratados, 0 pagados, 7 registrados, 0 asignaciones activas |
| T02 | Pagar T01 | 10 pagados, 7 asignaciones activas, 3 cupos pagados disponibles |
| T03 | Agregar 3 personas luego de T02 | 10 asignaciones activas, 0 libres |
| T04 | Ampliar 1 en tarifa regular | Nueva compra, precio regular congelado, sin imponer mínimo 10 |
| T05 | Intento Izipay fallido seguido de exitoso | Misma compra/orden, dos transacciones, derechos una sola vez |
| T06 | Callback exitoso duplicado | Ningún derecho duplicado |
| T07 | Juan juega fútbol y vóley en Dúo | Dos participaciones, una asignación en esa inscripción |
| T08 | Juan se intenta inscribir en fútbol de otra inscripción del mismo evento | Rechazo R11 |
| T09 | Juan en dos inscripciones distintas (distintos deportes), ambas con fiesta | Ambas compras conservan su cupo; una acreditación global, un QR útil |
| T10 | Retirar a Juan de inscripción A pero permanece en B | Liberar A, mantener fiesta si B la financia |
| T11 | Admin bloquea fiesta a Juan y luego paga otra compra | Bloqueo permanece |
| T12 | Admin concede fiesta a deportista sin pase | Acceso verdadero sin compra ficticia; motivo y actor auditables |
| T13 | Retirar jugador que aún juega otra disciplina en la misma inscripción | No liberar su cupo todavía |
| T14 | Intento de consumir el último cupo desde dos requests concurrentes | Solo una asignación exitosa |
| T15 | Dos escaneos simultáneos de QR de un uso | Solo un ingreso autorizado |
| T16 | Ampliación de Dúo | Más cupos y pases de fiesta, no otro box/caja |
| T17 | Equipo de promoción principal 2002 | Categoria Senior, según rango configurado |
| T18 | Fusión de promociones no permitida | Servicio rechaza creación/confirmación según política confirmada |
| T19 | Modificar precio después de compra | Compra y transacción conservan importe histórico |
| T20 | Responsable cambia participantes después de fecha límite | Rechazo del flujo normal |
| T21 | Intento de utilizar cupo pagado en Inscripción A para Inscripción B | Rechazo |
| T22 | Un jugador no firma aceptación requerida | No confirmar la habilitación que legalmente depende de esa aceptación |
| T23 | Edición 2027 con nuevos rangos | No modifica clasificación histórica confirmada de 2026 |

## 9. Preguntas y decisiones pendientes (no bloquear exploración; sí bloquear implementación que las presuponga)

1. **Ámbito histórico de `Categoria`:** resolver cómo versionar por `Evento` cuando cambian los rangos entre ediciones, sin volverla dependiente de `Disciplina`.
2. **Promoción fusionada:** cuál es diferencia máxima, cuándo se permite, categoría resultante en caso de conflicto; servicio configurable o regla operativa según aprobación. No crear tabla de reglas sin necesidad.
3. **Beneficios colectivos:** si hay asignación física/canje de box y cerveza, agregar modelo de estado por inscripción; confirmar unidad y responsable de entrega.
4. **Contratación de ampliaciones:** si se pueden agregar jugadores nuevos antes de pagar la ampliación (registrados pero no acreditados) o si se espera a cobrar para registrar; no deben obtener derechos antes de pago.
5. **Momento del precio:** fijación cuando se crea compra o cuando se inicia pago; vencimiento de cotizaciones/órdenes. Evitar cambio retroactivo.
6. **Pago manual/reembolsos:** aceptación de depósitos/comprobantes, anulaciones, pagos duplicados, devoluciones parciales/completas y autorización del comité.
7. **Flujo final de consentimiento:** quién acepta por cada jugador, versiones y prueba de aceptación; datos de seguro por evento si corresponde.
8. **Plazo de edición y excepciones de administradores** tras el cierre; qué acciones generan historial y revocación.
9. **Cardinalidad `Compra ↔ OrdenPago`** cuando una orden falla, vence o requiere reemisión; el diseño base permite varios intentos por orden.
10. **Desglose de acceso BOX individual:** si no hay torniquete/QR de zona box, no introducir `acceso_box` sin caso real.
11. **Estados definitivos e invariantes de `AcreditacionEvento`:** evitar contradicciones entre `estado`, `habilitado`, `acceso_fiesta` y override. Preferir estado/override + acceso efectivo calculado o materializado consistentemente.
12. **Capacidad máxima por equipo y por disciplina elegida:** tomar del catálogo validado; no confundir mínimo comercial con roster máximo.

## 10. Orden de trabajo esperado del agente de IA

**Entregable A — Exploración:** leer `contract`, auditar modelos y servicios, y elaborar matriz *regla acordada → tabla / FK / constraint / servicio / prueba*. Mostrar conflictos antes de implementar.

**Entregable B — Diseño:** ER final sin tablas opcionales no aprobadas, decisiones sobre campos redundantes para R11, estados/transiciones, invariantes de cupo y acreditación; incluir firmas/contratos de eventos o callbacks entre módulos (no integrar por importación inversa de `pagos` hacia `salesianos_fest`).

**Entregable C — Implementación incremental:** (1) catálogos y paquetes; (2) inscripción/equipos/personas/participación; (3) compra/orden/transacción/idempotencia; (4) asignaciones y acreditación; (5) consentimientos, accesos, auditoría; (6) seed y pruebas end-to-end. Comprobar cada bloque antes del siguiente.

**Entregable D — Calidad:** pruebas T01–T23, carreras de concurrencia, integridad por inscripción y evento, control de permisos, seguridad del QR, conciliación de pasarela. No afirmar completitud sin ejecutarlas.

**Entregable E — Migración/corte:** definir explícitamente si se preservan, archivan o migran los datos del módulo antiguo. Aunque el diseño se rehace desde cero, un despliegue puede requerir estrategia de convivencia/corte; no borrar información real sin autorización.

## 11. Antipatrones expresamente descartados

- Copiar todas las FK del modelo heredado por inercia.
- Crear `EventoDisciplina`, `ReglaFusionPromocion`, `EquipoPromocion` sin caso aprobado.
- Hacer `pagos` dependiente de `Inscripcion` de Salesianos Fest.
- Mezclar `Inscripcion.estado` con `Compra.estado` o marcar inscripción deportiva como confirmada solo por cobrar.
- Usar `AcreditacionEvento.acceso_fiesta` como prueba de que una inscripción posee un cupo.
- Convertir `PaqueteBeneficio` en un contador mutable de personas.
- Asignar cupos no pagados como si fueran activos.
- Crear N registros de cupos vacíos cuando una compra paga N personas: la cantidad la guarda `Compra`, las asignaciones solo vinculan ocupantes.
- Quitar el acceso global de una persona tras retirar solo uno de sus orígenes.
- Reactivar automáticamente a un bloqueado por administrador.
- Crear compras nuevas ante cada fallo de Izipay cuando la misma orden aún se puede reintentar.
- Cambiar precios históricos al editar tarifas futuras.

---

**Resultado esperado:** backend modular, determinista y auditable, cuyo saldo comercial pertenece a cada inscripción y cuyos accesos efectivos pertenecen a cada persona por evento, con el origen siempre recuperable y sin sobreingeniería para futuros tipos de eventos.
