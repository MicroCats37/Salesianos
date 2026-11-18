# Frontend 03 — Pases, tienda, checkout y recuperación de compra

**Concepto transversal:** cada módulo posee checkout propio, mientras el componente visual Izipay y el estado de orden se comparten. Nunca carrito mixto.

## PASS-01 — `/pases`

**Objetivo:** comprar entradas individuales de fiesta, sin inscripción deportiva ni cuenta obligatoria.

**Vista:** pase disponible, precio vigente confirmado, cantidad, resumen, entrada de DNI/correo de comprador mediante modal/formulario shadcn/ui, CTA “Continuar al pago”. Mostrar claramente que **comprador y asistentes pueden ser distintos**.

**Flujo:** elegir → datos → compra/orden → Izipay → confirmación → estado de pase → gestión/beneficiarios. **No exigir que ya existan todas las Personas destinatarias antes de pagar** (regla actual de lote tras pago). **Estados:** pasarela cerrada, pendiente, confirmado, aún verificando, fallo de pago, entradas pendientes de asignación. **Aceptación:** cerrar checkout no borra compra; beneficiarios no se asignan sobre compra no pagada.

## PASS-02 — `/pases/gestionar/[token]` (ruta conceptual)

**Objetivo:** permitir a comprador invitado asignar/revisar entradas sin crear cuenta. **Acceso:** token privado de uso/expiración controlados, posible revalidación por correo cuando corresponda.

**Vista:** resumen de compra, cantidad adquirida, asignada, pendiente y lista de personas. **Acciones:** resolver Persona por tipo/documento, asignar pase, revisar estado, revocar según PD-02. **Errores:** vínculo expirado, compra ajena, documento incorrecto, persona ya tiene derecho activo, asignación sin cupo, pase revocado. **Aceptación:** no exponer compras de terceros con DNI solamente.

## SHOP-01 — `/tienda`

**Objetivo:** descubrir productos propios de Salesianos FEST. **Bloques:** buscador opcional, filtros por categoría, tarjetas con imagen principal, precio/oferta, disponibilidad, CTA a detalle. **No mezclar** productos con paquetes deportivos ni entradas en un solo carrito.

**Estados:** sin productos, categoría vacía, agotado, error de imágenes, edición sin tienda. **Aceptación:** el catálogo no inventa stock disponible y las tarjetas usan fotos del servidor.

## SHOP-02 — `/tienda/[slug]`

**Vista:** carrusel de `ProductoImagen` ordenadas, título/descripción, categoría, precio normal/oferta activa, cantidad, disponibilidad, CTA “Comprar”. Miniaturas navegables con teclado y alt descriptivo.

**Flujo:** seleccionar cantidad → validar disponibilidad/precio en backend → datos comprador → crear `Pedido` + `Compra` + `OrdenPago` → pago → mostrar “Pedido pagado / pendiente de entrega” y ticket si aplica. **Importante:** el checkout de tienda está acotado a marketplace; puede incluir varios detalles del mismo dominio si se aprueba, nunca pases/cupos externos.

## SHOP-03 — `/tienda/pedidos/[token]`

**Objetivo:** seguir pedido invitado. **Bloques:** resumen, productos/cantidades, estado de pago, estado de entrega, código/QR cuando corresponda, historial de consumos permitidos. **Aceptación:** un pedido pagado sin entrega no aparece como “entregado”.

## REC-01 — `/recuperar-compra`

**Objetivo:** recuperar enlace privado por correo (proveedor pendiente). **UX:** solicitar correo y datos mínimos apropiados; respuesta neutra (“Si encontramos una compra asociada, recibirás instrucciones”). Nunca revelar si un DNI ajeno tiene entradas. **Estados:** enviado/pendiente/limitación de frecuencia/error temporal; no reabrir compra por enviar otro mensaje.

## Componente compartido de pago (sin ruta propia obligatoria)

**Componentes:** resumen de compra, estado de orden, modal Izipay, mensaje de verificación, botón “Consultar estado”, recuperación de orden. **Estados operativos comprensibles:**

| Estado presentado | Significado | CTA |
|---|---|---|
| Pago pendiente | Aún no hay confirmación de dinero | Continuar pago |
| Verificando pago | Resultado recibido, aún no concluyente | Consultar más tarde |
| Pago confirmado | Evidencia válida de cobro | Ver entradas/cupos/pedido |
| Pago no completado | Intento fallido, compra no pagada | Reintentar de forma segura |
| Necesita atención | Cobro probado pero derecho aún no habilitado | Contactar soporte / revisión admin |

**No:** borrar compra al cerrar modal; asumir pago desde mensaje del navegador; abrir cada vez un intento nuevo sin revisar los anteriores; mostrar “liquidación”, `CAPTURED`, tokens u otros estados del proveedor al usuario.

## Reglas de imagen (tienda/patrocinadores)

Django `ImageField` + volumen persistente; `ProductoImagen` ordenado y descripción alternativa; miniaturas/visualización desde servidor local. No CDN. La validación de archivo, persistencia y limpieza se especifica en arquitectura e integraciones.
