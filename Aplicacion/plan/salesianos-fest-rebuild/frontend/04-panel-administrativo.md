# Frontend 04 — Panel administrativo: módulos, acciones y estados

**Prioridad:** UX operativa; administrador único funcional con `Django Groups`, backend autoritativo y auditoría de acciones sensibles. No replicar vistas de lectura que no permiten resolver problemas.

## 1. Estructura del panel

**Navegación sugerida:** Resumen; Evento/edición; Inscripciones; Equipos y participantes; Competencias; Pagos; Pases e ingresos; Marketplace; Patrocinadores; Personas/usuarios; Validaciones/historial.

Para evitar barra lateral interminable, agrupar en secciones desplegables **Deportivo**, **Ventas y entradas**, **Configuración y personas**. Solo mostrar módulos activos de la edición, conservando acceso al histórico cuando el rol lo permita.

## 2. ADM-01 — Resumen operativo

**Mostrar:** edición seleccionada, inscripciones activas/pendientes, equipos incompletos, encuentros próximos, compras pendientes/de atención, entradas por validar, pedidos por entregar, alertas de stock. **Acciones:** navegar a listas filtradas desde métricas. No mostrar decenas de KPIs irrelevantes. **Estado vacío:** “Aún no hay inscripciones para esta edición”.

## 3. ADM-02/03/04 — Ediciones, personas y usuarios

- **Ediciones:** crear/editar/publicar/cerrar cuando reglas lo permitan; fechas y módulos habilitados. Branding diferido.
- **Personas:** buscar por documento y nombre, ver relaciones (participaciones, pases, compras visibles por permiso), confirmar datos encontrados en RENIEC. No crear duplicados.
- **Usuarios:** cuentas y grupo Normal/Administrador, activar/desactivar. Elevación de privilegio sujeta a autorización explícita; superusuario técnico no es rol ordinario configurable.

## 4. ADM-05/06 — Inscripciones

**Listado:** responsable, paquete, edición, equipos, estado comprensible, cupos (adquiridos/asignados/disponibles), pago relevante y alerta. **Filtros:** responsable, disciplina, estado, fecha, incidencia.

**Detalle dividido en pestañas:** Resumen, Equipos, Pool y personas, Compras de cupos, Historial. Las acciones administrativas permitidas deben explicar consecuencias. **Ejemplo:** “Retirar participante libera su cupo en esta inscripción; no genera devolución”.

## 5. ADM-07/08/09 — Equipos y participantes (rediseño prioritario)

La referencia actual lista equipos pero **no ofrece detalle clicable**, aunque ya existen datos de participantes. La reconstrucción **debe incorporar vista operativa de equipo**.

**Tabla de equipos propuesta:** Equipo, disciplina/categoría, responsable, plantilla actual, mínimo necesario, máximo, estado legible, motivo si no puede competir, acción “Ver equipo”. Reducir badges crípticos. **Detalle:** participantes con documento y estado, inscripción, cupos relacionados, elegibilidad, acciones autorizadas.

**Mensajes ideales:** “6 jugadores registrados; necesita al menos 7”, “No hay cupos deportivos disponibles”, “Este jugador ya participa en la misma disciplina”. Las reglas y motivos vienen del backend.

**Participantes:** buscar persona y ver participaciones por evento, equipo y disciplina; poder localizar conflictos y consultar historial, no duplicar paneles de usuario.

## 6. ADM-14 — Pagos (rediseño prioritario)

**Separar tres niveles:**

1. **Listado operativo:** Compra/orden, comprador, concepto, total, fecha y **un único estado comprensible**. Filtros por estado operativo, tipo de compra, fecha y texto.
2. **Detalle comercial:** Qué compró, pago en qué estado, qué obtuvo; siguiente acción permitida.
3. **Diagnóstico y auditoría:** Orden, intentos Izipay, evidencia, operaciones manuales. Oculto por defecto bajo pestaña avanzada.

**Ejemplos de acciones:** consultar pago, revisar incidencia, registrar pago externo (si está permitido), auditar cancelación o revocación. **No:** “Aprobación manual” como botón ubicuo sin contexto, mezclar cancelar pago con retirar participantes, llamar “liquidado” al beneficio entregado.

**Información que el presenter debe aportar:** `estado_operativo.codigo` y `etiqueta`, `descripcion`, `accion_recomendada`, `derechos_otorgados/resumen`, `puede_operar` según permisos. El cliente no infiere el estado a partir de `OrdenPago`/`Compra`/`TransaccionPago`.

## 7. ADM-15/16 — Pases e ingreso

**Pases:** catálogo, compras, beneficiarios, asignaciones pendientes, cortesías sin pago, revocaciones auditadas. **Ingreso:** lector QR/código y vista previa de derecho; **confirmar ingreso** separado de leer; texto claro de inválido/consumido/revocado/no permitido. No mostrar tokens en listados.

## 8. ADM-17/18/19/20 — Marketplace

**Productos:** CRUD de título, descripción, categoría, precio/oferta opcional, estado, imágenes/carrusel (`ImageField`). **Pedidos:** pagado / pendiente de entrega / entregado, y detalle. **Inventario:** ver existencias, historial de movimiento y operaciones de entrada, merma, consumo interno y salida sin venta con motivo. **Entregas:** escanear/código, revisar productos/cantidades, confirmar entrega, impedir doble canje.

## 9. ADM-21 — Patrocinadores

CRUD de ficha, logo, galería de imágenes ordenada, relación con edición, visibilidad. No administrar aportaciones monetarias ni comisiones mientras no sean requisito.

## 10. ADM-22 — Historial de validaciones

Buscar por ticket/código, persona, compra/referencia, tipo de derecho, fecha, operador, veredicto y punto. No confundir **validación de entrada** con **confirmación de pago**.

## 11. Carencias de referencia que debemos corregir

Fuente `03b-paginas-administrativas-y-operativas.md`:

- Equipo: no hay drilldown pese a esquema de detalle existente.
- Pagos: backend admite `estado_operativo` pero la UI no expone ese filtro; se confunden capas de compra/orden/evidencia.
- Competencias: escritura distribuida entre detalle y cuadro.
- Varias capacidades declaradas de administración no corresponden a rutas utilizables; en el nuevo diseño definimos acciones reales, no permisos vacíos.
- Mensajes/campos como `personas[]` para inscripciones y códigos técnicos deben corregirse en presenters/contratos, no taparse con hacks en componentes.

## 12. Criterios de aceptación del panel

1. Desde un problema visible en resumen se llega a su registro filtrado y acción concreta.
2. Desde lista de equipos se abre detalle y se entiende por qué no está listo para competir.
3. Un pago se explica sin mirar registros técnicos; detalles del proveedor se ven solo bajo diagnóstico.
4. Todo cambio sensible muestra confirmación con efecto y motivo cuando corresponda.
5. Un 403 de backend impide ejecución aunque alguien fuerce el botón desde el cliente.
6. Tabla/página funciona en móvil con búsqueda y acciones accesibles; no depende de hover.
