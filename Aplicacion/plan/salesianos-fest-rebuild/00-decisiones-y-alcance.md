# 00 — Decisiones, alcance y puntos abiertos

**Estado:** especificación funcional v0.1. **Regla:** no convertir propuestas en decisiones aprobadas sin revisión.

## 1. Visión y límites

**[ACORDADO]** Salesianos FEST es el primer evento. La plataforma separa `Evento` (familia/nombre) y `Edicion` (año y calendario) para compartir funcionalidades entre ediciones sin mezclar históricos. En el futuro podría incorporar otros eventos, reutilizando los módulos adecuados, **sin construir ahora un motor universal**.

**[ACORDADO]** Las funciones son opcionales por evento/edición cuando tenga sentido (inscripciones, competencias, pases, marketplace, etc.); no todos los eventos deben tener disciplinas, tarifas o pases. Se posterga branding configurable. No fijar hoy categorías, precios, tarifas ni cupos concretos.

**[ACORDADO]** Reconstrucción orientada a **mejorar el flujo y UX**, no replicar páginas actuales. Hay un agente local especializado que adaptará estas especificaciones al proyecto real. Las pruebas se escriben junto con el código, pero se ejecutan en la etapa final de integración y validación.

## 2. Registro de decisiones confirmadas

| ID | Área | Decisión acordada |
|---|---|---|
| DEC-01 | Ediciones | Datos independientes por edición; módulos, personas y cuentas reutilizables |
| DEC-02 | Roles | `Persona` independiente de `Usuario`. Grupos Django: usuario normal y administrador. Superusuario solo técnico |
| DEC-03 | Identity lookup | Buscar `Persona` por tipo/documento localmente; si no existe, consultar servicio RENIEC; persistir al confirmar operación real |
| DEC-04 | Compras sin cuenta | Permitir compras sin crear necesariamente un `Usuario`; DNI no equivale a autenticación; vínculo privado de recuperación por email |
| DEC-05 | Inscripción | `Inscripcion` posee pool de cupos deportivos: inicial + ampliaciones pagadas; responsable asigna/reasigna participantes |
| DEC-06 | Cupos | Cupo pagado no asignado queda disponible; retiro puede liberarlo para reutilización en la misma inscripción; no implica reembolso |
| DEC-07 | Beneficios | Distinguir `PaqueteBeneficio` (oferta) de asignaciones y derechos efectivos; FIESTA individual, BOX grupal, otros futuros no obligatorios |
| DEC-08 | Pases | Mantener conceptos `Pase`, `CompraPase`, `PaseBeneficiario`; revisar reglas de revocación y trazabilidad del origen |
| DEC-09 | Cortesía | Administrador puede otorgar entrada gratuita con auditoría, sin inventar pago ni compra comercial |
| DEC-10 | Checkout | Cada dominio crea compras con su propio endpoint/servicio: inscripción, pase, tienda; **no carrito conjunto ni un pedido multi-dominio** |
| DEC-11 | Comercio/pagos | Infraestructura compartida `Compra`, `OrdenPago`, `TransaccionPago`, Izipay; derechos se habilitan solo tras pago verificado, una vez |
| DEC-12 | Checkout resiliente | Cerrar modal no cancela compra; reabrir no duplica compra; los intentos y estados se resuelven desde backend |
| DEC-13 | Marketplace | Tienda propia del organizador, sin vendedores externos; productos, categorías, varias imágenes y gestión del stock |
| DEC-14 | Imágenes | Django `ImageField` y almacenamiento local persistente servido por la aplicación/proxy; **sin CDN** para productos/patrocinadores |
| DEC-15 | Inventario | Auditar ventas, reposiciones, entregas gratuitas, consumos y ajustes; una salida sin pago no es compra ficticia |
| DEC-16 | Precios tienda | Precio normal fijo; oferta opcional, temporal si se necesita; evitar motor de precios complejo |
| DEC-17 | Patrocinadores | Datos de patrocinador, logo y galería ordenable de varias imágenes |
| DEC-18 | Validación/tickets | Validación posterior a la compra, independiente de cobro; lector QR reusable; **pantallas separadas** para ingreso y entrega; backend decide y registra consumo |
| DEC-19 | Admin | Panel integrado por tareas; especial énfasis en UX de pagos, equipos, partidos/encuentros y mensajes claros |
| DEC-20 | API/UX | Presenters y wrappers legibles; términos internos como “liquidación” **no deben mostrarse como etiqueta principal de UI** |
| DEC-21 | Correo | Proveedor SMTP (Gmail u otro), límites y configuración **pospuestos hasta el final** |

## 3. Diferenciar productos, derechos y operaciones

**[ACORDADO]** No todo lo pagado equivale a una entrada; no todo beneficio es individual. Una compra de inscripción otorga **cupos deportivos**, cuyos participantes pueden obtener FIESTA según el paquete. BOX puede ser grupal. Comprar un pase individual y otorgar cortesía son otros orígenes de ingreso. Los tickets representan **cómo acreditar/canjear** un derecho; no sustituyen cupos, beneficios ni compras.

**[ACORDADO]** Marketplace tiene pedidos comerciales propios y registro de stock. La entrega/consumo sucede después, con reglas separadas. Una compra pagada no significa necesariamente producto entregado.

## 4. Preguntas todavía abiertas

| ID | Pendiente | Decisión que afecta | Bloquea |
|---|---|---|---|
| PD-01 | BOX: ¿se asigna a responsable, equipo o grupo definido? ¿cómo se utiliza? | Asignación y eventual canje grupal | Detalle de BOX, no núcleo de inscripciones |
| PD-02 | Pases: ¿revocar antes del uso libera la asignación? ¿se permite reemplazar titular? | Reglas de `PaseBeneficiario` | Flujo de revocación |
| PD-03 | Ticket: ¿1 código por unidad o ticket con cantidad y consumo parcial? | Validación por producto | Consumo parcial |
| PD-04 | Acceso: ¿una entrada válida una vez, por día o con reingresos? | Control de acceso | Reglas finales de escaneo |
| PD-05 | Inventario: ¿stock compartido entre ediciones o separado por edición? | Modelo de stock | Modelo definitivo de existencia |
| PD-06 | Cancelación/reembolso: cuándo se permiten, efecto sobre cupos, entradas y productos | Pagos y dominios | Reembolsos/cancelaciones avanzadas |
| PD-07 | Compras anónimas: definir ámbito definitivo de guest checkout (inscripción vs pases/tienda) | UX/autenticación | Inscripción como invitado |
| PD-08 | Correo: proveedor, plantillas, límites, reintentos y entrega | Notificaciones | Envío real, no compras |
| PD-09 | Beneficios de paquete y ampliación: qué se recalcula por cupo y qué se otorga una sola vez | Beneficios adicionales | Algunos paquetes |
| PD-10 | Alcance exacto de modificaciones administrativas, motivos, autorizaciones y devoluciones | Operación admin | Acciones sensibles específicas |

## 5. Fuera de alcance en esta versión

- Multivendedor, comisiones de terceros, carrito que mezcle inscripciones, pases y tienda.
- Branding editable y motor de tematización por edición.
- Definición definitiva de precios, disciplinas, promociones, límites de jugadores y tarifas.
- Implementar una tienda con variantes complejas, múltiples almacenes o programas de fidelización sin requerimiento.
- Tratar QR como autorización por sí solo: el QR/código identifica un derecho, no valida la operación por arte de magia.
- Cerrar ahora arquitectura de archivos, base de datos definitiva ni elección SMTP.

## 6. Criterios transversales

1. El **backend es autoridad** en permisos, precios, disponibilidad, cupos, derechos, cobros y consumo.
2. Todo acto sensible debe poder auditarse (actor, momento, motivo y referencia).
3. Ningún cambio en browser garantiza que el cobro ocurrió; solo confirmación confiable del proveedor o evidencia administrativa autorizada.
4. Un hecho financiero debe conservar su historia aunque se cancele/retire un derecho derivado.
5. Frontend muestra estados comprensibles y siguientes acciones, no códigos internos desnudos.
6. Toda ruta nueva del frontend tiene ficha de usuario + flujo + datos + criterios de aceptación.
7. Se distinguen visiblemente los requisitos aprobados, propuestas y pendientes.

## 7. Referencias actuales utilizadas

- Arquitectura/modelos: `04-datos-y-dominio(1).md` (identidad, FEST, commerce, pagos, competencias).
- Flujos: `05-flujos-end-to-end(1).md`, `02b-proposito-y-consumidores-de-endpoints.md`.
- Pantallas y carencias: `03a-paginas-publicas-y-compra.md`, `03b-paginas-administrativas-y-operativas.md`, `07-guia-para-ui-ux(1).md`.
