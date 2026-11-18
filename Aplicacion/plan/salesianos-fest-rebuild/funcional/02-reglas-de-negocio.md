# Funcional 02 — Reglas de negocio transversales

**Lectura:** reglas `RN` son objetivo; `PD` indica regla pendiente de decisión. Todos los números de los paquetes seed existentes son referencia y **no tarifas aprobadas**.

## 1. Ediciones, personas y roles

- **RN-E01** Una edición pertenece a un evento y conserva inscripciones, competencias, precios, pases y operaciones históricas propios.
- **RN-E02** Las funcionalidades optativas se habilitan por evento/edición según la configuración que finalmente se acuerde; una edición sin marketplace no necesita productos ni pedidos.
- **RN-U01** Una Persona puede existir sin Usuario; el mismo documento identifica la persona en años distintos.
- **RN-U02** Los grupos Django de negocio son Normal y Administrador; `is_superuser` es técnico. La autorización también comprueba **titularidad**, no solo rol.
- **RN-U03** Resolver documento: buscar local; si no existe, consultar fuente externa; confirmar la operación antes de persistir la persona. Evitar duplicados ante solicitudes concurrentes.
- **RN-U04** DNI es un identificador, no una credencial que autorice ver una compra de terceros.

## 2. Inscripciones y cupos

- **RN-I01** Cada inscripción tiene un responsable y se vincula a una edición/paquete y a sus equipos/participantes.
- **RN-I02** Una compra inicial o ampliación **pendiente** no habilita cupos; al confirmarse, se incorporan al pool **una sola vez**.
- **RN-I03** `saldo_disponible = cupos_pagados_vigentes - asignaciones_activas` (sujeto a cancelaciones válidas). Un saldo nunca es negativo.
- **RN-I04** Retirar participante puede liberar su asignación para otro de la misma inscripción; no anula compra, ni devuelve dinero, ni aumenta el inventario de un evento.
- **RN-I05** La elegibilidad, topes, solapamientos y participación duplicada se verifican siempre en backend, con protección contra carreras.
- **RN-I06** Comprar cupos extra **no** duplica automáticamente beneficios `FIJO_INICIAL`; beneficios `POR_CUPO` obedecen sus reglas comerciales. **[PD-09]** Reglas completas por tipo a cerrar.

## 3. Pases, beneficios, acceso y tickets

- **RN-P01** `PaqueteBeneficio` define beneficios **ofrecidos**; no es la lista de usos efectivamente disfrutados.
- **RN-P02** FIESTA puede provenir de pase comprado, paquete deportivo pagado o cortesía autorizada. Se conserva origen y estado de cada derecho.
- **RN-P03** BOX es un beneficio grupal diferente de los cupos deportivos. Su titularidad/uso exactos quedan abiertos (**PD-01**).
- **RN-P04** `PaseBeneficiario` sigue siendo una entidad válida para asignar una entrada comprada a una Persona. El comprador y quien asiste pueden ser distintos.
- **RN-P05** Administrador puede otorgar entrada gratuita con actor, fecha y motivo; no simular un cobro de S/ 0.
- **RN-P06** Un ticket/QR identifica un derecho validable; escanear no equivale a usar, hasta confirmación de la operación.
- **RN-P07** Consumo/ingreso deja registro auditado. No se permite consumir simultáneamente más unidades de las autorizadas; reintentos son idempotentes.
- **RN-P08** Cancelar o revocar un derecho invalida sus validaciones futuras; los consumos ya ocurridos permanecen en historial.
- **PD-02/03/04** Reglas pendientes: reasignación de pases revocados, tickets parciales, reingresos/días.

## 4. Commerce y pagos

- **RN-C01** Cada dominio tiene endpoint y flujo propios para crear compras; infraestructura comercial compartida, sin carrito combinado.
- **RN-C02** El precio y total se calculan/validan en servidor y se congelan para la compra; el cliente no impone un importe.
- **RN-C03** Cerrar/recargar modal no equivale a cancelar compra u orden.
- **RN-C04** Antes de crear otro intento, consultar estado de orden/intento existente. Preservar trazabilidad de todo intento.
- **RN-C05** Solo evidencia confiable del proveedor o aprobación manual autorizada permite declarar pago confirmado.
- **RN-C06** Confirmaciones duplicadas/tardías no generan dobles cupos, pases, movimientos de stock ni correos duplicados.
- **RN-C07** Mostrar al comprador “Pago pendiente”, “Pago confirmado”, “Pago no completado” o “Estamos verificando tu pago”; **no mostrar “liquidación” como lenguaje principal**.
- **RN-C08** Cobro confirmado y entrega del derecho son hechos separados; ante error de activación, se conserva pago confirmado y el sistema registra una incidencia recuperable.
- **PD-06** Reembolso/cancelación posterior a pago necesita política explícita por dominio.

## 5. Marketplace e inventario

- **RN-M01** Tienda oficial del organizador; ningún vendedor tercero, tarifa de comisión o payout por tercero.
- **RN-M02** Producto puede tener categoría, precio normal, oferta opcional y 0..N imágenes (`ImageField`, servidor propio).
- **RN-M03** Pedido y su detalle registran cantidades y precio aplicado; el histórico no cambia por una nueva oferta.
- **RN-M04** Todo movimiento de inventario indica producto, signo/cantidad, motivo, referencia origen y actor cuando es manual.
- **RN-M05** Salida por regalo, merma o consumo interno no es pago ni orden ficticia.
- **RN-M06** Evitar sobreventa: reservar temporalmente o proteger disponibilidad dentro de transacción; no descontar dos veces por webhook.
- **RN-M07** Pagado y entregado son estados diferentes. La validación de entrega puede ser posterior y parcial **solo si se aprueba ese uso**.
- **PD-05** Existencias compartidas vs edición individual requiere definición.

## 6. Competencias y administración

- **RN-K01** Participar en torneo exige pertenencia y elegibilidad deportiva verificables; comprar no equivale a estar asignado en un equipo.
- **RN-K02** Encuentros tienen programación, participantes, resultado, vencedor, estado y auditoría; correcciones que afecten fases posteriores requieren vista previa y confirmación explícita.
- **RN-K03** Nunca solapar un equipo en dos encuentros al mismo horario cuando la disciplina/regla lo prohíba.
- **RN-A01** Admin puede listar, filtrar y operar entidades conforme a su autorización. La UI oculta acciones, pero el backend autoriza definitivamente.
- **RN-A02** Toda acción sensible expone resultado comprensible (qué cambió, qué no cambió, siguiente acción) y justifica impedimentos.
- **RN-A03** Errores de validación vinculan el campo problemático cuando sea posible y no filtran rastros, SQL ni secretos.

## 7. Reglas de prueba de aceptación

Para cada `RN`, la documentación de tarea debe asociar mínimo un caso exitoso, un caso de rechazo y, cuando corresponda, concurrencia/repetición. No transformar estos casos en lógica duplicada del frontend.
