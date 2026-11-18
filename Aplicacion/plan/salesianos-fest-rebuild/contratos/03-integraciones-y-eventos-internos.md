# Contratos 03 — Integraciones externas y coordinación interna

**Propósito:** especificar responsabilidades de integración, no seleccionar librería o bus de mensajes aún.

## 1. Izipay (proveedor de pago)

**[ACORDADO]** Los dominios compran mediante sus endpoints. Commerce registra `Compra`; pagos gestiona `OrdenPago` y `TransaccionPago`. El proveedor confirma cobro. El módulo de origen habilita sus propios derechos **idempotentemente**.

**Obligaciones:**

- Orden separada de intentos del proveedor.
- Reabrir checkout no genera otra compra; consultar estado válido de orden/sesión antes de renovar intento.
- Cerrar modal no significa cancelar.
- Notificación firmada y verificada; no confiar solo en browser.
- Repetición o llegada tardía no duplica derechos.
- La UI diferencia pago fallido vs estado incierto vs pago confirmado.
- Error de aplicación de cupos/pases/productos posterior al cobro es incidencia visible y recuperable, no reversión silenciosa del cobro.

**[REFERENCIA ACTUAL]** El sistema auditado inicia nuevos intentos al reabrir modal, y el archivo `.env` auditado no mostraba `IZIPAY_KEY_HASH`; son aspectos a revisar en la implementación, no reglas deseadas.

## 2. Coordinación de activación: interfaz lógica

```text
CompraCreada(origen, compra_id, orden_id)
PagoVerificado(orden_id, evidencia)
CompraMarcadaPagada(compra_id)
ActivarDominio(compra_id, origen)
  origen=INSCRIPCION  -> habilitar cupos
  origen=PASE         -> habilitar lote de entradas
  origen=MARKETPLACE  -> confirmar pedido/stock
NotificarComprador(compra_id) [opcional y reintentable]
```

**No es obligación implementar un broker.** Son pasos de negocio con garantías. Un coordinador transaccional/servicio de aplicación local puede resolverlos. Si se usa cola/outbox, debe garantizar idempotencia.

## 3. RENIEC / fuente documental

- Servicio existente independiente vía HTTP, referenciado por `usuarios`.
- Buscar Persona primero localmente; externa solo cuando falta y corresponde.
- No grabar cada consulta externa como registro definitivo.
- Tiempo de espera, datos faltantes, fuente indisponible y documento no encontrado se presentan como estados distintos.
- Registrar origen/fecha de datos recuperados si se requiere control de calidad.

## 4. Correo

**[ACORDADO: DIFERIDO]** Se necesita notificación y recuperación por email; **NO** se decide ahora Gmail vs proveedor transaccional ni sus credenciales, cuotas o SMTP. El servicio `notificaciones` recibe una petición abstracta y conserva posibilidad de reintento.

**Regla crítica:** fallo de correo **no** anula pago ni revierte cupos o entradas. En futuras fases elegir plantillas, remitente, dominio, límites, observabilidad y política de reenvíos.

## 5. Imágenes en Django (sin CDN)

Productos y patrocinadores utilizan `ImageField` y relación 1:N para imágenes ordenadas. Almacenamiento en servidor con volumen persistente; exposición web mediante servicio/servidor de archivos de despliegue. El agente de arquitectura define copia de seguridad, permisos, validación de MIME/tamaño, borrado seguro y manejo de nombres.

## 6. Ticket y validación

- La credencial puede representarse con QR o código alfanumérico seguro; **la credencial es un identificador, no una decisión de autorización**.
- Un preview consulta estado y derecho real; no lo consume.
- La confirmación consulta y consume con bloqueo/atomicidad e idempotencia, guardando actor, instante, tipo/cantidad y resultado.
- Pases y marketplace comparten lector y servicio básico de validación; la operación específica determina reglas y visibilidad.
- Una compra pendiente no produce derecho canjeable; revocación posterior impide nuevas validaciones, manteniendo historial de usos anteriores.

## 7. Reglas de fallo y recuperación

| Incidente | Recuperación esperada |
|---|---|
| Doble webhook | Ignorar efecto duplicado; responder de forma idempotente |
| Modal cerrado | Mantener compra/orden; permitir continuar |
| Activación de derecho falla | Registrar incidencia con pago pagado; reintento seguro de activación |
| RENIEC falla | Permitir reintento y mensaje; no fabricar identidades |
| Envío email falla | Reintentar notificación sin repetir cobro |
| Ticket ya consumido | Resultado seguro con información de uso para operador autorizado |
| Dos validadores escanean a la vez | Solo un consumo efectivo dentro de límite |
| Foto deja de existir en disco | Degradar galería con aviso y registrar incidencia de media |

## 8. Seguridad operativa

Claves Izipay, credenciales SMTP, tokens de enlaces y QR no se registran en logs públicos ni se devuelven en listas. Distinguir referencia visible de identificador secreto. Controles de rate limiting para recuperación/documentos/escaneo se diseñarán en arquitectura.
