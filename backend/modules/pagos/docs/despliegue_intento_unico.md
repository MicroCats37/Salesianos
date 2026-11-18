# Despliegue de la restricción de intento único (pagos)

> **Módulo:** `backend/modules/pagos`
> **Cambio:** `admin-payment-evidence-retry-safety` — Apply 3 (Fase 3)
> **Invariante:** una orden de pago tiene, como máximo, **un intento vivo** (`PENDIENTE`).

---

## 1. Qué introduce esta fase

| Pieza | Tipo | Qué hace |
|---|---|---|
| `verificar_intentos_pago` | Comando de **solo lectura** | Informa las órdenes que ya tienen más de un intento vivo. No modifica ningún registro. |
| `0006_transpaccionpago_intento_activo_unico` | Migración | Instala el índice único parcial y solo si los datos están limpios. |
| `uniq_transpago_activo_orden` | Restricción del modelo | `UNIQUE (orden_pago_id) WHERE status = 'PENDIENTE'`. |

El índice es **parcial**: deja intactos los intentos cerrados (`EXITO`, `FALLIDO`,
`CANCELADO`). La traza de auditoría de la orden nunca se reescribe y ningún
intento se borra.

---

## 2. Requisitos previos

1. **El código del ciclo de vida de intentos ya está desplegado** (Apply 2). El
   flujo retira el intento vivo y crea el nuevo dentro de la *misma*
   transacción, con la fila de la orden bloqueada. Sin ese código, la
   restricción rechazaría la preparación del checkout.
2. La configuración del proveedor está presente en el entorno (ver §7 — solo
   los *nombres* de las variables).

> La restricción es la **red de seguridad**; la garantía primaria es el flujo
> atómico. La restricción no reemplaza al flujo: lo vuelve indefendible.

---

## 3. Orden de despliegue

### Paso 1 — Preflight (obligatorio, en cada entorno)

```bash
python manage.py verificar_intentos_pago
```

| Código de salida | Significado | Acción |
|---|---|---|
| `0` | Ninguna orden tiene más de un intento vivo | Continuar con el paso 3 |
| `1` | Hay órdenes con más de un intento vivo | **Detener el despliegue** y resolver (paso 2) |

Informe estructurado (para el pipeline de despliegue):

```bash
python manage.py verificar_intentos_pago --json
```

### Paso 2 — Resolución explícita de las órdenes inseguras

El preflight **nunca** borra, cancela ni retira intentos: un intento de pago es
un registro de auditoría y puede ser dinero en vuelo. La resolución es manual
y explícita:

1. **Reconciliar con el proveedor**: determinar cuál de los intentos vivos
   corresponde a un pago real (o a ninguno).
2. **Retirar explícitamente los intentos sobrantes** — conservar siempre el
   intento que corresponde al pago:

   ```sql
   UPDATE pagos_transaccionpago
   SET status = 'CANCELADO', updated_at = <marca de tiempo>
   WHERE orden_pago_id = '<uuid de la orden>'
     AND status = 'PENDIENTE'
     AND transaction_id <> '<intento que se conserva>';
   ```

   `CANCELADO` es el estado con el que el propio flujo retira un intento
   superado: el intento se conserva, deja de estar vivo y la traza permanece.
3. **Repetir el preflight** hasta que salga con código `0`.

> Para órdenes ya pagadas, el comando revisado `reconciliar_pagos` cierra los
> intentos vivos obsoletos (admite `--dry-run`). No aplica a órdenes
> `PENDIENTE`: esas se resuelven con el paso 2.

### Paso 3 — Instalación de la restricción

```bash
python manage.py migrate pagos
```

La migración **vuelve a comprobar los datos** antes de instalar el índice: si
encuentra una orden con más de un intento vivo, aborta sin modificar la base
de datos e indica el comando a ejecutar. El índice nunca borra ni modifica
intentos.

### Paso 4 — Verificación

```bash
python manage.py verificar_intentos_pago    # debe salir con código 0
python manage.py verificar_pagos             # diagnóstico de evidencia de pago
```

---

## 4. Condiciones de rollback

| Situación | Acción |
|---|---|
| La migración se rechaza por datos inseguros | **No reviertas**: resuelve las órdenes del paso 2 y vuelve a aplicarla. El código funciona sin el índice. |
| El índice bloquea una operación legítima | Revierte la migración (`migrate pagos 0005`) e investiga el caso. |
| Errores de la aplicación tras la migración | Revierte la migración y después el código (§5). |
| El preflight devuelve código `1` | No apliques la migración. |

---

## 5. Reversión

```bash
python manage.py migrate pagos 0005
```

La reversión elimina **solo el índice**. No modifica ningún dato: los intentos
siguen siendo la traza de auditoría que siempre fueron.

> ### ⚠️ Orden de reversión
>
> Revierte **primero la migración** y **después el código**. El código
> anterior al Apply 2 reutilizaba el intento vivo en lugar de retirarlo: con
> el índice instalado, ese código podría intentar crear un segundo intento
> vivo y el índice lo rechazaría.

---

## 6. Notas operativas

- El índice nunca borra datos: `EXITO`, `FALLIDO` y `CANCELADO` quedan fuera
  de su condición, así que la traza de la orden se conserva íntegra.
- Una orden con **cero** intentos vivos es válida: el índice no la afecta.
- El preflight es de solo lectura y se puede ejecutar las veces que haga falta
  (por ejemplo, antes de cada ventana de despliegue).
- El informe `--json` no expone la sesión del proveedor (`metadata`): solo
  expone el identificador de la orden y los identificadores de los intentos.

---

## 7. Variables de entorno

Solo los **nombres**. Los valores jamás se documentan, se registran en un
ticket ni se pegan en un registro de despliegue.

| Variable | Para qué |
|---|---|
| `IZIPAY_SHOP_ID` | Código de comercio del proveedor |
| `IZIPAY_KEY` | Clave pública de la API del proveedor |
| `IZIPAY_KEY_HASH` | Clave del comercio para verificar la firma del proveedor |
| `IZIPAY_API_URL` | URL base del proveedor |
| `IZIPAY_CALLBACK_URL` | URL de retorno del SDK del proveedor |

> Mientras `IZIPAY_KEY_HASH` no esté configurada, el proveedor no puede
> autenticarse y la confirmación del navegador se acepta sin verificación de
> firma (con aviso en el log). El despliegue comercial sigue bloqueado hasta
> que la clave del comercio esté entregada.
