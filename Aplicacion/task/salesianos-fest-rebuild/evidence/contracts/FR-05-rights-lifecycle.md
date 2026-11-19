# FR-05 — Ciclo de vida de derechos: preview / confirm / revoke

**Freeze:** `FREEZE-RT-1.0.0` · **Propietario:** A4 (pases/beneficios) + A5 (marketplace) + A8 (validaciones) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `RN-P01`..`RN-P08`, `RN-M07` · `DEC-07`, `DEC-08`, `DEC-09`, `DEC-18` · plan `contratos/01` §5, `contratos/03` §6, `funcional/02` §3, `funcional/04` FL-07, FL-10

---

## 1. Modelo de derecho

Un **derecho** es la concesión efectiva que habilita a participar, ingresar o canjear. Es propiedad de **un** módulo dueño y nunca se duplica.

| Concepto | Módulo dueño | Nota |
|---|---|---|
| Cupo deportivo pagado | `inscripciones` | No es pase ni entrada (`DEC-07`) |
| Entrada de pase asignada | `pases` / `beneficios` | `PaseBeneficiario` — el beneficiario puede diferir del comprador (`RN-P04`) |
| Beneficio grupal (BOX) | `pases` / `beneficios` | Titularidad **abierta** (`PD-01`, `RN-P03`) |
| Entrega de producto comprada | `marketplace` | Pagado ≠ entregado (`RN-M07`) |
| Entrada de cortesía | `pases` / `beneficios` | `CortesiaEntrada` — con actor, fecha y motivo (`RN-P05`, `DEC-09`) |

**Prohibiciones:**

1. **Prohibido** que el módulo `validaciones` cree, conceda o modifique derechos. Verifica contra el módulo dueño (`funcional/01` §1).
2. **Prohibido** que un `Ticket` duplique el derecho. El ticket es **una credencial que referencia** un derecho existente (`funcional/03` §1, `RN-P06`).
3. **Prohibido** que `AsignacionCupo` se convierta en `PaseBeneficiario` por automatismo sin regla explícita (`funcional/03` §3).

## 2. Las tres operaciones — contrato congelado

### 2.1 `Preview` — lectura, sin efecto

| Aspecto | Regla congelada |
|---|---|
| Efecto | **Ninguno**. No muta, no consume, no crea registro de validación |
| Entrada | Código/credencial + contexto (pases, marketplace) |
| Salida | Tipo de derecho, titular, estado, cantidad disponible, `puede_canjear`, motivo si no se puede |
| Idempotencia | Trivial: es lectura |
| Autorización | Operador autenticado con permiso operativo |

`puede_canjear` y `motivo` los calcula el **módulo dueño del derecho**, no `validaciones` (`funcional/01` §5).

### 2.2 `Confirm` — mutación atómica e idempotente

| Aspecto | Regla congelada |
|---|---|
| Efecto | Consume el derecho y **registra** el consumo |
| Atomicidad | Reconsulta y consume bajo bloqueo transaccional. El backend **vuelve a validar** en el momento del confirm, no confía en el preview (`FL-10` paso 4) |
| Idempotencia | Clave de idempotencia obligatoria (`FR-04` §2.2). Una repetición devuelve el resultado de la primera ejecución |
| Concurrencia | Dos validadores simultáneos ⇒ **un solo** consumo efectivo dentro del límite (`RN-P07`) |
| Registro | Actor, instante, tipo/cantidad, resultado. La validación **queda en el historial** |
| Exceso | Si la cantidad solicitada excede la disponible → `409` con código estable. **Prohibido** consumir parcialmente sin que el operador lo solicite explícitamente |

### 2.3 `Revoke` — invalidación permanente y auditada

| Aspecto | Regla congelada |
|---|---|
| Efecto | Invalida el derecho para **validaciones futuras** |
| Historial | Los consumos ya ocurridos **permanecen** (`RN-P08`) |
| Auditoría | Actor, instante, motivo, referencia. Obligatoria |
| Idempotencia | Revocar dos veces no es un error; informa el estado final |
| Alcance | Se revoca **el derecho de origen**. Un derecho derivado que lo referencie deja de ser canjeable por esa vía |
| Economia | El slot **no** se devuelve. `DEC-06`: liberar un cupo para reasignar dentro de la misma inscripción **no** es un reembolso ni aumenta inventario |

**Observación de referencia (no ratificada).** El código congelado documenta que la revocación de un pase es permanente y **no** devuelve el slot (`02b` línea 603). Ese comportamiento se registra como `[REFERENCIA ACTUAL]`; la regla comercial de reasignación sigue en `PD-02` → `GOV-01-OPEN-08`. Este freeze congela **la interfaz** de revocación, no la política comercial.

## 3. Forma congelada de las respuestas de derechos

### 3.1 Preview

```json
{
  "success": true,
  "data": {
    "tipo_derecho": "PASE",
    "codigo": "PASE_FIESTA",
    "titular": { "persona_id": "…", "nombre": "…" },
    "edicion_id": "…",
    "estado": "HABILITADO",
    "cantidad_total": 1,
    "cantidad_disponible": 1,
    "cantidad_consumida": 0,
    "puede_canjear": true,
    "motivo_codigo": null,
    "motivo_mensaje": null
  },
  "error": null,
  "message": null
}
```

| Campo | Regla |
|---|---|
| `tipo_derecho` | `PASE` \| `ENTRADA_CORTESIA` \| `PRODUCTO` \| `INSCRIPCION` — discriminante del módulo dueño |
| `codigo` | código del concepto de derecho, no un UUID |
| `estado` | estado del derecho tal como lo publica el módulo dueño |
| `cantidad_total` / `cantidad_disponible` / `cantidad_consumida` | presentes en todos los casos. Expresan el **partial consumption** de forma que `PD-03` no obligue a cambiar el contrato |
| `puede_canjear` | booleano calculado en backend |
| `motivo_codigo` / `motivo_mensaje` | presentes cuando `puede_canjear = false`. Mensaje público seguro |

### 3.2 Confirm

```json
{
  "success": true,
  "data": {
    "validacion_id": "…",
    "tipo_derecho": "PASE",
    "cantidad_consumida": 1,
    "cantidad_restante": 0,
    "estado": "CANJEADO",
    "consumido_en": "2026-11-18T15:04:05Z",
    "actor": { "usuario_id": "…", "persona_id": "…" },
    "repetido": false
  },
  "error": null,
  "message": "El ingreso se registró correctamente."
}
```

| Campo | Regla |
|---|---|
| `validacion_id` | identificador del registro de validación/canje |
| `cantidad_consumida` / `cantidad_restante` | cuantitativo del canje |
| `repetido` | `true` cuando la operación es una repetición idempotente de una ejecución previa. **No** es un error: la primera ejecución y la repetición devuelven el mismo `data` |

### 3.3 Revoke

```json
{
  "success": true,
  "data": {
    "derecho_id": "…",
    "estado": "REVOCADO",
    "revocado_en": "2026-11-18T15:10:00Z",
    "actor": { "usuario_id": "…", "persona_id": "…" },
    "motivo": "Solicitud del responsable de la inscripción.",
    "ya_revocado": false
  },
  "error": null,
  "message": "El derecho se revocó correctamente."
}
```

`ya_revocado` cubre la idempotencia de la revocación sin lanzar error.

## 4. Reglas transversales de derechos

| Regla | Contenido |
|---|---|
| `RN-P01` | `PaqueteBeneficio` define beneficios **ofrecidos**. No es el derecho enjoyed |
| `RN-P02` | FIESTA puede provenir de pase comprado, paquete deportivo pagado o cortesía autorizada. Se conserva **origen y estado** de cada derecho |
| `RN-P05` | La cortesía registra actor, fecha y motivo. **Prohibido** simular un cobro de S/ 0 ni crear orden/transacción de pago ficticia (`FL-07` paso 3) |
| `RN-P06` | Escanear **no** equivale a usar. El preview no consume |
| `RN-P07` | Consumo auditado; no se permite consumir más unidades de las autorizadas; reintentos idempotentes |
| `RN-P08` | Cancelar o revocar invalida validaciones futuras; los consumos pasados permanecen |
| `RN-M07` | Pagado y entregado son estados distintos. La validación de entrega puede ser posterior y parcial **solo si se aprueba ese uso** (`PD-03` sigue abierto) |
| Regla transversal 4 | Un hecho financiero conserva su historia aunque se cancele un derecho derivado |

## 5. Interfaz entre módulos

`funcional/01` §5, congelada:

| Interfaz | Productor | Consumidor | Resultado |
|---|---|---|---|
| `VerificarDerecho` | `pases`/`beneficios`/`marketplace` | `validaciones` | Puede usar/canjear, con razón y límite |

**Prohibido** que `validaciones` reimplemente reglas de dominio (`funcional/01` §1). **Prohibido** que un pase/entrada se interprete como permiso Django: el grupo autoriza a operar el sistema; el derecho autoriza a participar/ingresar/canjear (`contratos/02` §6).

## 6. Consumo del freeze

| Consumidor | Depende de | Acción |
|---|---|---|
| FND-05 (`T-015`) | `T-013` | Activación de derechos por `(compra_id, origen)`
| DOM-03 (`T-030`..`T-032`) | este freeze | Pases, beneficiarios, cortesía: `puede_canjear`, `origen`, revocación |
| DOM-06 (`T-043`) | este freeze | Pedido pagado vs entregado; validación de entrega |
| XCT-01 (`T-080`, `T-081`) | este freeze | Preview y confirm con las tres formas congeladas; consumos auditados |

## 7. Criterios de aceptación de este freeze

- [x] Preview **no** muta; Confirm es atómico e idempotente; Revoke es permanente, auditado e idempotente.
- [x] Los tres derechos y su módulo dueño, con las prohibiciones de duplicación.
- [x] Las tres formas de respuesta congeladas, con cantidad explícita para no prejuzgar `PD-03`.
- [x] La interfaz `VerificarDerecho` con productor y consumidor nombrados.
- [x] `PD-01`, `PD-02`, `PD-03`, `PD-04` quedan **abiertos** y no prejuzgados por la forma congelada.

## 8. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-08` | Reglas de `PaseBeneficiario` al revocar: liberar asignación, reemplazo de titular (`PD-02`) | A4 + producto |
| `PD-01` | Titularidad y uso de BOX | A4 + producto |
| `PD-03` | Ticket por unidad vs con cantidad y consumo parcial | A4 + A8 + producto |
| `PD-04` | Alcance de validez de una entrada (una vez, por día, reingresos) | A8 + producto |
