# FR-04 — Commerce, pagos e idempotencia

**Freeze:** `FREEZE-CM-1.0.0` · **Propietario:** A2 (módulo `pagos`) + A0 (activación) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `RN-C01`..`RN-C08` · `DEC-10`, `DEC-11`, `DEC-12` · plan `contratos/03-integraciones-y-eventos-internos.md` §1–§2, `funcional/02` §4

---

## 1. Agregado comercial y agregados de pago

### 1.1 `Compra` — dueño: `commerce`

| Atributo | Regla congelada |
|---|---|
| `id` | UUID (pk) |
| `persona_id` | FK → `Persona` — **el comprador**. Obligatoria. Una compra **siempre** tiene comprador persona |
| `origen` | `INSCRIPCION` \| `PASE` \| `MARKETPLACE`. **Tres** orígenes, uno por dominio. No existe "compra genérica sin origen" |
| `estado` | `PENDIENTE` \| `PAGADA` \| `CANCELADA` |
| `total` | `Decimal` congelado en el momento de la compra. **Prohibido** calcularlo en el cliente (`RN-C02`) |
| `moneda` | código ISO-4217 en string (`"PEN"`). **Prohibido** `float` para montos |
| `lineas_snapshot` | snapshot inmutable de lo comprado (producto/paquete/pase, cantidad, precio unitario, precio aplicado). **No cambia** aunque el precio vigente cambie después (`RN-M03`) |
| `orden_pago_id` | FK → `OrdenPago`, nullable mientras `estado = PENDIENTE` |
| `creada_en`, `actualizada_en` | timestamps |

**Prohibiciones del agregado:**

1. **Prohibido** un carrito conjunto: no existe una compra que mezcle orígenes (`DEC-10`, `RN-C01`).
2. **Prohibido** una compra sin `origen`. El dominio de origen decide cómo se habilita el derecho.
3. **Prohibido** recalcular `total` o `lineas_snapshot` después de creada. Una corrección comercial es una compra/ajuste nueva con su propio rastro (`RN-M03`, criterio transversal 4).

### 1.2 `OrdenPago` — dueño: `pagos`

| Atributo | Regla congelada |
|---|---|
| `id` | UUID (pk) |
| `compra_id` | FK → `Compra` |
| `estado` | `PENDIENTE` \| `EN_VERIFICACION` \| `CONFIRMADA` \| `FALLIDA` \| `VENCIDA` |
| `monto`, `moneda` | deben coincidir **exactamente** con `Compra.total` / `Compra.moneda` |
| `referencia` | referencia **visible** del proveedor. **Prohibido** exponer secretos, tokens de sesión ni payloads firmados en listas (`contratos/03` §8) |

### 1.3 `TransaccionPago` — dueño: `pagos`

| Atributo | Regla congelada |
|---|---|
| `id` | UUID (pk) |
| `orden_pago_id` | FK → `OrdenPago` |
| `intento` | número de intento, creciente por orden |
| `referencia_proveedor` | identificador del intento. Visible solo en detalle técnico autorizado |
| `estado` | `PENDIENTE` \| `EXITO` \| `FALLIDO` \| `CANCELADO` |
| `verificada` | `bool` — la notificación fue firmada y verificada |
| `evidencia` | evidencia de la aprobación manual, cuando aplica (`AprobacionPagoManual`) |

**Regla de separación:** `Compra.estado` (hecho comercial), `OrdenPago.estado` (hecho de orden) e `TransaccionPago.estado` (hecho del proveedor) son **tres hechos distintos**. El veredicto que ve el operador lo calcula `pagos` (`EstadoOperativoPagoService`) y se publica como `estado_operativo` (`FR-01` §5). El frontend **nunca** cruza los tres hechos (`contratos/01` §1.4).

## 2. Idempotencia — garantías congeladas

`RN-C06`, `DEC-11`, `DEC-12`, `contratos/03` §1.

### 2.1 Garantías

| `#` | Garantía | Mecanismo congelado | Regla observable |
|---|---|---|---|
| I-1 | **Una** confirmación efectiva por orden | La confirmación verifica la firma **antes** de mutar; el estado `CONFIRMADA` se alcanza una sola vez | Reintento o notificación tardía **no** duplica derechos, movimientos de stock ni correos |
| I-2 | **Una** activación de derechos por compra | La activación se identifica por `(compra_id, origen)` y es idempotente | Reintentar la activación converge; no agrega cupos, pases ni confirma pedidos dos veces |
| I-3 | **Un** registro de stock por confirmación | El movimiento de inventario se identifica por la referencia de la confirmación | Doble webhook **no** descuenta dos veces (`RN-M06`) |
| I-4 | Reabrir el checkout **no** crea otra compra | Antes de crear un intento se consulta el estado de orden/sesión existente (`RN-C04`) | El mismo flujo de compra conserva su `compra_id` y su `orden_pago_id` |
| I-5 | Cerrar el modal **no** cancela | El cierre del navegador no emite ninguna orden de cancelación (`RN-C03`) | La compra sigue `PENDIENTE` y es recuperable |
| I-6 | Aprobación manual idempotente | Si ya existe aprobación activa, la operación no escribe y responde con el código de ya-aprobada | No se duplica la prueba de pago |
| I-7 | Asignación y consumo idempotentes | Reasignación de un cupo liberado reactiva en vez de duplicar; el consumo concurrente se serializa | Un solo consumo efectivo dentro del límite (`RN-P07`) |

### 2.2 Clave de idempotencia en el borde HTTP

Toda mutación que pueda repetirse (crear compra, confirmar canje, registrar movimiento, activar) **debe** aceptar una clave de idempotencia explícita:

| Aspecto | Regla congelada |
|---|---|
| Transporte | Header `Idempotency-Key` (string opaco, ≤ 128 caracteres). Alternativa aceptada en cuerpos de mutación de canje: campo `idempotency_key` |
| Formato | UUID v4 o equivalente aleatorio generado **por el cliente en cada intención de negocio**, no por intento de red |
| Ámbito | Por endpoint + actor. Dos claves distintas ⇒ dos operaciones distintas |
| Reutilización | **Prohibido** reutilizar la misma clave para dos operaciones de negocio distintas. La clave identifica **una intención**, no una sesión |
| Efecto de repetición | La operación devuelve el **mismo resultado** (mismo `data`, mismo `success`), con HTTP de la primera ejecución. Nunca 500 |
| Conflictto | Misma clave, payload distinto → `409 IDEMPOTENCY_KEY_REUTILIZADA` |

### 2.3 Secuencia de activación (congelada)

`contratos/03` §2. Orden obligatorio, sin omitir pasos:

```
CompraCreada(origen, compra_id, orden_id)
PagoVerificado(orden_id, evidencia)         # firma verificada o aprobación manual autorizada
CompraMarcadaPagada(compra_id)              # idempotente
ActivarDominio(compra_id, origen)            # idempotente por (compra_id, origen)
  origen=INSCRIPCION -> habilitar cupos
  origen=PASE        -> habilitar lote de entradas
  origen=MARKETPLACE -> confirmar pedido y stock
NotificarComprador(compra_id)                # opcional y reintentable
```

**No es obligación** un broker de mensajes. Un coordinador transaccional o un servicio de aplicación local puede resolver los pasos. Si se usa cola/outbox, **debe** garantizar idempotencia (I-2).

## 3. Evidencia de pago y confianza (congelada)

`RN-C05` / `contratos/03` §1.

| Fuente de confirmación | ¿Declara el pago pagado? | Requisitos |
|---|---|---|
| Notificación del proveedor | **Sí** | Firma verificada **antes** de mutar; orden y monto coincidentes |
| Aprobación manual autorizada | **Sí** | Interruptor explícito habilitado; actor, monto, moneda, canal, referencia y motivo auditados; monto y moneda **exactamente** iguales a los de la orden |
| Estado devuelto por el navegador | **No** | El navegador no es fuente de confianza (`criterio transversal 3`) |
| Cierre del modal / timeout | **No** | No implica pago fallido ni cancelado (`RN-C03`, `contratos/01` §7) |

**Prohibido** declarar el pago confirmado por ausencia de evidencia. La UI distingue: *pago pendiente*, *pago confirmado*, *pago no completado*, *estamos verificando tu pago* (`RN-C07`).

## 4. Pago confirmado y entrega del derecho son hechos separados

`RN-C08`: ante error de activación posterior al cobro, el pago confirmado **se conserva** y el sistema registra una **incidencia recuperable**. No hay reversión silenciosa del cobro, ni activación ficticia.

| Situación | Comportamiento congelado |
|---|---|
| Cobro ok, activación falla | `Compra.estado = PAGADA`; `OrdenPago.estado = CONFIRMADA`; se registra incidencia con reintento seguro; la UI muestra "Pago confirmado; estamos resolviendo la activación de tu compra" (`contratos/01` §7), **nunca** `settlement_status` |
| Cobro ok, entrega de producto pendiente | `Pedido` pagado y stock confirmado; la **entrega** es un hecho posterior y separado (`RN-M07`) |

## 5. Reembolsos y cancelaciones

`PD-06` sigue **abierto**. Este freeze congela lo que **no** depende de la política:

1. La reversión de derechos, si existe, es un **derecho nuevo con estado `REVOCADO`**, no un borrado. El historial se conserva (`RN-P08`, criterio transversal 4).
2. `Compra.estado = CANCELADA` **no** reembolsa por sí sola.
3. La política por dominio (cuándo se permite, efecto sobre cupos/entradas/productos) **no se ratifica aquí** → `GOV-01-OPEN-06`.

## 6. Consumo del freeze

| Consumidor | Depende de | Acción |
|---|---|---|
| FND-04 (`T-013`, `T-014`) | este freeze | `Compra` en `commerce`, `OrdenPago`/`TransaccionPago` en `pagos`, claves de idempotencia, catálogo de errores de pago |
| FND-05 (`T-015`) | `T-013` | Activación idempotente por `(compra_id, origen)` y la secuencia §2.3 |
| DOM-01, DOM-03, DOM-05 | `T-013`, `T-014` | Cada dominio crea su propia compra por su endpoint; **prohibido** el carrito conjunto |
| XCT-03 (`T-084`) | `T-014`, `T-015`, `T-023`, `T-031`, `T-043` | Conciliación de pagos: separar los tres estados y la incidencia de activación |

## 7. Criterios de aceptación de este freeze

- [x] `Compra`, `OrdenPago` y `TransaccionPago` con identificadores, atributos yowners nombrados.
- [x] Idempotencia con garantías I-1..I-7, clave de idempotencia y reglas de conflicto.
- [x] Secuencia de activación ordenada e idempotente.
- [x] Fuentes de confirmación de pago y su confianza, con la prohibitions del navegador.
- [x] Separación entre pago confirmado y entrega del derecho.
- [x] `PD-06` (reembolsos) registrado como **abierto**, sin ratificar política.

## 8. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-06` | Política de cancelación/reembolso por dominio (`PD-06`) | A2 + producto |
| `GOV-01-OPEN-07` | Nombre del proveedor SMTP y política de correo — **diferido por `DEC-21`** | A0 + producto |
| `PD-09` | Recálculo de beneficios por cupo frente a beneficios de una sola vez (`FIJO_INICIAL`) | A4 + producto |
