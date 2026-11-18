# Contratos 01 — API, wrappers, presenters y mensajes

**Estado:** contrato UX/API **propuesto**. No es una declaración de endpoints existentes ni de su forma final. El agente de arquitectura podrá ajustar nomenclatura y tipos preservando el comportamiento.

## 1. Principios

1. Un solo esquema consistente de respuesta y errores; el frontend no debe recibir 4 formatos distintos según módulo.
2. Controllers exponen interfaces; services aplican reglas; presenters componen representaciones orientadas a un **caso de uso concreto**.
3. Una lectura para tabla no necesita contener todos los detalles técnicos; el detalle se consulta por separado.
4. El frontend nunca infiere estado final de negocio cruzando `Compra.estado`, `OrdenPago.estado`, mensajes Izipay y banderas locales.
5. Códigos estables para máquinas; etiquetas y explicaciones claras para usuarios.
6. La UI no muestra como texto principal palabras técnicas como `liquidación`, `settlement`, `captured`, ni UUID del proveedor.

## 2. Envelope recomendado

La referencia actual utiliza `ApiResponse { success, data, error, message }`; la paginación se anida en `data` con `items,total,page,page_size,total_pages`. **[PROPUESTO]** Mantener una forma única o acordar una evolución de la misma antes de que los agentes creen APIs nuevas.

```json
{
  "success": true,
  "data": { "items": [], "total": 0, "page": 1, "page_size": 25, "total_pages": 0 },
  "message": "Consulta completada"
}
```

En error: HTTP correcto, error `code`, mensaje para usuario, detalles de campos opcionales sin exponer trazas internas.

```json
{
  "success": false,
  "error": {
    "code": "TEAM_MINIMUM_NOT_MET",
    "message": "El equipo necesita al menos 7 jugadores para competir",
    "field_errors": []
  }
}
```

La forma exacta de `error` puede conservar la del sistema actual o evolucionar, **pero debe ser única y documentada**.

## 3. Ejemplo de presenter administrativo: equipo

```json
{
  "id": "uuid",
  "nombre": "Equipo Norte",
  "disciplina": { "id": "uuid", "nombre": "Fútbol 7" },
  "categoria": { "id": "uuid", "nombre": "Senior" },
  "plantilla": { "registrados": 6, "minimo": 7, "maximo": 10 },
  "estado_operativo": {
    "codigo": "INCOMPLETO",
    "etiqueta": "Falta 1 jugador",
    "descripcion": "Se necesita al menos 7 jugadores para competir"
  },
  "acciones_disponibles": ["VER_PARTICIPANTES", "AGREGAR_PARTICIPANTE"]
}
```

El servidor calcula la causa; el cliente únicamente formatea. No confundir máximo de plantilla con saldo de cupos pagados.

## 4. Ejemplo de presenter administrativo: pago

```json
{
  "compra_id": "uuid",
  "orden_pago_id": "uuid",
  "tipo_compra": "INSCRIPCION",
  "resumen_concepto": "Ampliación de 5 cupos deportivos",
  "comprador": { "persona_id": "uuid", "nombre": "Ejemplo" },
  "monto": "250.00",
  "moneda": "PEN",
  "estado_operativo": {
    "codigo": "PAGO_CONFIRMADO",
    "etiqueta": "Pago confirmado",
    "descripcion": "La operación ha sido cobrada correctamente"
  },
  "entrega_derechos": {
    "codigo": "CUPOS_HABILITADOS",
    "etiqueta": "5 cupos disponibles en la inscripción"
  },
  "acciones_disponibles": ["VER_INSCRIPCION", "VER_HISTORIAL"]
}
```

Importes y datos son **ilustrativos**. Intentos del proveedor, referencias y firmas aparecen solo en el detalle técnico con autorización. Nunca devolver secretos de Izipay ni tokens de sesión.

## 5. Contratos de caso de uso (propuestos)

| Servicio/endpoint conceptual | Actor | Entrada | Presenter de salida |
|---|---|---|---|
| Resolver documento local→RENIEC | Visitante autenticado o flujo habilitado | tipo/documento | Persona resuelta o datos externos con origen |
| Crear compra de cupos | Responsable | inscripción, cantidad, paquete | compra+orden+estado+efecto esperado |
| Obtener pool | Responsable/admin | inscripción | pagados, activos, disponibles, equipos, impedimentos |
| Comprar pase | Comprador cuenta/invitado | pase, cantidad, comprador | compra+orden, beneficiarios pendientes |
| Asignar pase | Titular del lote/admin | compra, persona | acceso asignado, pendientes |
| Crear pedido tienda | Comprador | producto(s) tienda, cantidades | pedido, snapshot, pago pendiente |
| Registrar movimiento stock | Admin | producto, tipo, cantidad, motivo | stock actualizado, movimiento id |
| Preview ticket | Operador | código, contexto pases/tienda | tipo, estado, cantidad, puede_canjar, motivo |
| Confirmar canje | Operador | ticket, idempotency, cantidad | consumido, restante, historial |
| Registrar resultado | Admin | encuentro, ganador, score, versión | encuentro y siguientes acciones |
| Preview corrección | Admin | encuentro, resultado propuesto | impacto, bloqueos, revisión requerida |

Las **rutas concretas** se definirán en un inventario generado desde estas operaciones y revisado con la especificación UX, en lugar de copiarlas de los 111 endpoints existentes.

## 6. Semántica de acciones disponibles

`acciones_disponibles` es una **proyección orientativa** de lo permitido y viable al momento de lectura. No reemplaza autorización ni validaciones del comando; toda mutación puede fallar por cambios de estado posteriores. No usarlo como fuente de seguridad.

## 7. Contratos de estados

- Separar compra `PENDIENTE/PAGADA/CANCELADA` de estado de intento Izipay y de entrega de derechos.
- Mensajes de UI siempre incluyen siguiente paso, por ejemplo “Pago confirmado; asigna tus 3 entradas”.
- Si hay discrepancia entre pago y derechos, mostrar “Pago confirmado; estamos resolviendo la activación de tu compra”, sin exponer `settlement_status`.
- No derivar “Pago fallido” por cierre de modal o timeout.
- En lista de equipos presentar `etiqueta` + causa y números; no inferir incompletitud en cliente.

## 8. Validación runtime y schemas

- Zod/validación frontend alineada con backend; un drift de contratos debe ser visible y testeable.
- Campos no opcionales definidos explícitamente; `null` != ausente.
- Errores `422` por campo; `409` por conflicto de negocio/versión; `401` auth; `403` permisos; 5xx error del servidor.
- Fechas en ISO con política de zona horaria documentada; montos preferentemente decimal/string para evitar pérdida de precisión.

## 9. Estado de referencia

La auditoría actual documenta dos estilos de espejo de datos y rutas que devuelven wrappers poco útiles. `03b` identifica pagos con filtro `estado_operativo` no expuesto; `03a` identifica clientes HTTP duplicados; `07-guia-para-ui-ux(1).md` exige que la autoridad de reglas sea backend. En la reconstrucción estas limitaciones **se corrigen con diseño de contrato y UX**, no parches aislados.
