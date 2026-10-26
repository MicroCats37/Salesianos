# Plan de Reconstrucción Limpia del Módulo Commerce

> **Proyecto**: Salesianos FEST  
> **Fecha**: 19 de octubre de 2026  
> **Estado**: Plan de SDD Explore  
> **Persistencia**: `sdd/commerce-refactor-clean-rebuild/explore`

---

## Resumen Ejecutivo

El módulo `commerce` tiene un campo mal nombrado (`orden_pago_fk` en lugar de `orden_pago`), un `related_name` que crea una referencia inversa no deseada desde `pagos.OrdenPago`, y el comando seed tiene un bug que impediría su ejecución. Este plan documenta el estado roto actual, el estado destino correcto, y los pasos de implementación para un refactor limpio.

---

## 1. Auditoría de Estado Roto

### 1.1 Problema Central

El campo `orden_pago_fk` en `commerce.Compra` viola:

1. **Convención Django**: el sufijo `_fk` es redundante — Django ya genera `orden_pago_fk_id` como columna de base de datos.
2. **Requisito explícito del usuario**: el campo debe llamarse `orden_pago`.
3. **Restricción arquitectónica**: `related_name="compra_comercial"` crea `orden_pago.compra_comercial` — una referencia inversa desde `pagos.OrdenPago` a `commerce.Compra`. **Viola la regla**: "`pagos.OrdenPago` has NO FK/OneToOne back to Compra".

### 1.2 Bug Crítico en Seed

```python
# seed_commerce.py línea 320 — ESTO ROMPE
orden_pago, op_created = OrdenPago.objects.get_or_create(
    compra=compra,  # ← OrdenPago no tiene campo 'compra'!
    defaults={...}
)
```

El modelo `OrdenPago` en `pagos` **no tiene** campo `compra`. Este código fallaría en tiempo de ejecución.

### 1.3 Resumen de Archivos Afectados

| Categoría | Cantidad | Archivos |
|-----------|----------|----------|
| ALTER (campo rename) | 1 | `commerce/domain/models/compra.py` |
| UPDATE (código Python) | 4 | `compra_core_service.py`, `seed_commerce.py`, `crear_compra_flujo.py`, `iniciar_pago_flujo.py` |
| VERIFY (funcionan sin cambios) | 5 | `compra_presenter.py`, `compra_selector.py`, `asignacion_cupo.py`, `compra_inscripcion.py`, `pago.py` |
| MIGRATION (nova) | 1 | `commerce/0002_rename_orden_pago_fk_to_orden_pago.py` |

---

## 2. Modelo ER Destino (Correcto)

```
commerce.Compra
├── id: UUID (PK)
├── responsable: FK → usuarios.Persona (nullable)
├── descripcion: CharField
├── referencia_externa: CharField
├── total: Decimal
├── estado: PENDIENTE/PAGADA/CANCELADA
└── orden_pago: OneToOne → pagos.OrdenPago  ← NOMBRE CORRECTO
    # Sin related_name → Sin back-ref en OrdenPago

pagos.OrdenPago
├── id: UUID (PK)
├── numero: CharField(unique)
├── monto_total: Decimal
├── moneda: CharField
├── estado: PENDIENTE/PAGADA/CANCELADA/VENCIDA
├── pagada_en: DateTime
├── expires_at: DateTime
├── descripcion: CharField (snapshot audit)
├── referencia_externa: CharField (snapshot audit)
└── metadata: JSONField (snapshot audit)
    # NO tiene related_name a commerce.Compra

salesianos_fest.CompraInscripcion
├── compra: OneToOne → commerce.Compra
├── inscripcion: FK → Inscripcion
├── tipo: INICIAL / AMPLIACION
├── cantidad: PositiveInteger
├── precio_unitario: Decimal (snapshot)
├── total: Decimal (snapshot)
└── Constraint: unique (inscripcion, tipo) WHERE tipo='INICIAL'

salesianos_fest.AsignacionCupo
├── inscripcion: FK → Inscripcion
├── compra: FK → commerce.Compra
├── inscripcion_persona: FK → InscripcionPersona
├── estado: ACTIVA / LIBERADA / REVOCADA
└── Constraint: unique (inscripcion, inscripcion_persona) WHERE estado='ACTIVA'
```

---

## 3. Campos y Metadatos de OrdenPago

### 3.1 Campos de Audit/Display (Snapshots)

Cuando se crea `OrdenPago` desde `salesianos_fest`, se populan:

```python
orden_pago.descripcion = f"Compra {tipo_display} - {paquete.nombre}"
orden_pago.referencia_externa = f"FEST-{str(inscripcion.id)[:8]}"
```

### 3.2 Metadatos Permitidos en `OrdenPago.metadata`

```python
METADATA_ALLOWED_KEYS = [
    "inscripcion_id",      # UUID de la inscripción
    "paquete_id",          # UUID del paquete
    "paquete_nombre",      # Nombre para display
    "evento_id",          # UUID del evento
    "buyer_documento",     # DNI (audit)
    "buyer_nombres",       # Nombres (audit)
    "buyer_apellidos",     # Apellidos (audit)
]
```

**PROHIBIDO**: tokens de sesión, passwords, secrets.

---

## 4. Dirección de Dependencias de Módulos

```
usuarios
  └── Persona
       └── commerce.Compra.responsable (FK nullable)

commerce
  ├── Compra
  │   └── orden_pago: OneToOne → pagos.OrdenPago
  └── CompraCoreService

pagos (AGNÓSTICO — no importa commerce ni salesianos_fest)
  ├── OrdenPago
  │   # Sin related_name a commerce.Compra
  ├── TransaccionPago
  │   └── orden_pago: FK → OrdenPago
  ├── IzipayCoreService
  └── PagosOrchestrator

salesianos_fest
  ├── CompraInscripcion
  │   ├── compra: OneToOne → commerce.Compra
  │   └── inscripcion: FK → Inscripcion
  ├── AsignacionCupo
  │   └── compra: FK → commerce.Compra
  ├── CrearCompraFlujo
  ├── IniciarPagoFlujo
  └── ConfirmarPagoFlujo
```

---

## 5. Secuencia de Migración

### 5.1 Migración Nueva

**Archivo**: `commerce/migrations/0002_rename_orden_pago_fk_to_orden_pago.py`

```python
import django.db.models.deletion
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("commerce", "0001_initial"),
    ]
    operations = [
        migrations.RenameField(
            model_name="compra",
            old_name="orden_pago_fk",
            new_name="orden_pago",
        ),
    ]
```

### 5.2 Orden de Apply

```
1. python manage.py migrate commerce
2. python manage.py shell -c "from commerce.models import Compra; print(Compra._meta.get_field('orden_pago').name)"
   → Debe imprimir: orden_pago
```

### 5.3 Rollback

```bash
python manage.py migrate commerce 0001_initial
```

---

## 6. Qué ELIMINAR vs ALTERAR

### 6.1 ALTERAR (refactor in-place)

| Archivo | Cambio |
|---------|--------|
| `commerce/domain/models/compra.py` | Renombrar `orden_pago_fk` → `orden_pago`; quitar `related_name="compra_comercial"` |
| `commerce/domain/services/core/compra_core_service.py` | Líneas 55, 65, 89: `orden_pago_fk` → `orden_pago` |
| `commerce/management/commands/seed_commerce.py` | Fix bug `compra=compra`; líneas 257, 332-334: `orden_pago_fk` → `orden_pago` |
| `salesianos_fest/domain/services/flujos/crear_compra_flujo.py` | Líneas 136-137: `orden_pago_fk` → `orden_pago` |
| `salesianos_fest/domain/services/flujos/iniciar_pago_flujo.py` | Línea 97: `orden_pago_fk` → `orden_pago` |

### 6.2 NO ELIMINAR (arquitectura correcta)

- Ningún archivo de migrations previo
- Ningún modelo existente

### 6.3 POR CONSTRUIR (módulo incompleto)

| Archivo | Estado Actual |
|---------|--------------|
| `commerce/domain/services/flujos/` | Vacío |
| `commerce/domain/services/orchestrators/` | Vacío |
| `commerce/presentation/controllers/` | Vacío |
| `commerce/tests/` | No existe |

---

## 7. Flujo Atómico de Creación

```python
# CrearCompraFlujo._crear_compra_sync (decorado con @transaction.atomic)
with transaction.atomic():
    # 1. Validar Inscripcion
    inscripcion = Inscripcion.objects.filter(id=data.inscripcion_id).first()
    
    # 2. Obtener precio vigente
    precio_unitario = _obtener_precio_vigente(inscripcion.paquete_id)
    
    # 3. Validar mínimo (solo INICIAL)
    if data.tipo == TipoCompraChoices.INICIAL:
        if data.cantidad < inscripcion.paquete.minimo_compra_inicial:
            raise CantidadInsuficienteError()
    
    # 4. Calcular total
    total = data.cantidad * precio_unitario
    
    # 5. Crear commerce.Compra (sin orden_pago aún)
    commerce_compra = Compra.objects.create(
        responsable=inscripcion.responsable,
        descripcion=descripcion,
        referencia_externa=referencia_externa,
        total=total,
        estado=EstadoCompraChoices.PENDIENTE,
    )
    
    # 6. Crear pagos.OrdenPago (sin parámetro 'compra')
    numero_orden = izipay_core.generar_numero_orden()
    orden_pago = izipay_core.crear_orden_pago(
        numero=numero_orden,
        monto_total=total,
        moneda="PEN",
    )
    
    # 6b. Poblar descripcion y referencia_externa (snapshots)
    orden_pago.descripcion = descripcion
    orden_pago.referencia_externa = referencia_externa
    orden_pago.save(update_fields=["descripcion", "referencia_externa", "updated_at"])
    
    # 7. Asignar OrdenPago a Compra (OneToOne desde el lado commerce)
    commerce_compra.orden_pago = orden_pago
    commerce_compra.save(update_fields=["orden_pago", "updated_at"])
    
    # 8. Crear CompraInscripcion
    compra_inscripcion = CompraInscripcion.objects.create(
        compra=commerce_compra,
        inscripcion=inscripcion,
        tipo=data.tipo,
        cantidad=data.cantidad,
        precio_unitario=precio_unitario,
        total=total,
    )
    
    # 9. Return
    return CompraCreatedResult(...)
```

---

## 8. Restricciones FEST

### 8.1 CompraInscripcion — Una Inicial, N Ampliaciones

```python
# En compra_inscripcion.py Meta.constraints
UniqueConstraint(
    fields=["inscripcion", "tipo"],
    condition=Q(tipo=TipoCompraChoices.INICIAL),
    name="unique_inicial_por_inscripcion",
)
```

### 8.2 Flujo de Confirmación de Pago (Idempotente)

```python
# ConfirmarPagoFlujo._confirmar_sync (con @transaction.atomic + select_for_update)
with transaction.atomic():
    compra = Compra.objects.select_related("orden_pago", "compra_inscripcion").select_for_update().filter(
        orden_pago_id=orden_pago_id
    ).first()
    
    # Idempotente: si ya PAGADA, retornar sin error
    if compra.estado != EstadoCompraChoices.PENDIENTE:
        return CompraConfirmedResult(success=True, already_confirmed=True)
    
    # Marcar PAGADA
    compra.estado = EstadoCompraChoices.PAGADA
    compra.save(update_fields=["estado", "updated_at"])
    
    return CompraConfirmedResult(success=True, already_confirmed=False)
```

---

## 9. Impacto Backend y Frontend

### 9.1 Endpoints Involucrados

| Método | Ruta | Impacto |
|--------|------|---------|
| POST | `/api/compras/` | Ninguno — usa IDs en JSON |
| GET | `/api/compras/{id}/` | Ninguno — usa IDs |
| GET | `/api/compras/inscripcion/{id}/` | Ninguno |
| POST | `/api/compras/{id}/iniciar-pago` | Ninguno |
| POST | `/api/compras/confirmar-pago` | Ninguno |
| GET | `/pagos/ordenes/{id}/` | Devuelve `orden_pago_id` en JSON |

### 9.2 Frontend — Archivos Involucrados

- `frontend/src/features/pagos/components/IzipayModal.tsx` — Llama `/api/pagos/izipay/preparar/`
- `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx` — Muestra compras

**Nota**: El frontend usa TypeScript types con IDs (UUIDs), no nombres de campos Django. No requiere cambios.

---

## 10. Diseño del Comando Seed

### 10.1 Bug Actual vs Corregido

```python
# ACTUAL (buggy) — seed_commerce.py
orden_pago, op_created = OrdenPago.objects.get_or_create(
    compra=compra,  # ← ERROR: OrdenPago no tiene campo 'compra'
    defaults={...}
)

# CORREGIDO
orden_pago = OrdenPago.objects.create(
    numero=f"ORD-{uuid.uuid4().hex[:10].upper()}",
    monto_total=total,
    moneda="PEN",
    estado=orden_pago_estado,
    descripcion=descripcion,
    referencia_externa=referencia_externa,
)
# Luego asignar
compra.orden_pago = orden_pago
compra.save(update_fields=["orden_pago", "updated_at"])
```

### 10.2 Invocación

```bash
#顺序:
python manage.py seed_catalogo_fest  # Primero (evento + paquetes)
python manage.py seed_commerce       # Segundo (compras + OrdenPagos)

# Reset completo:
python manage.py seed_commerce --clear
```

---

## 11. Matriz de Tests

### 11.1 Tests Existentes

| Archivo | Cobertura | Requiere Cambio |
|---------|-----------|-----------------|
| `salesianos_fest/tests/integration/test_compra.py` | Compilation + basic | Sí — refs `orden_pago_fk` |
| `salesianos_fest/tests/integration/test_inscripcion.py` | F1 happy path | No |
| `salesianos_fest/tests/integration/test_asignacion.py` | Cupos post-pago | No |

### 11.2 Tests por Crear

```
commerce/tests/
├── __init__.py
├── conftest.py
├── factories.py              # make_compra_payload()
└── integration/
    ├── __init__.py
    ├── conftest.py
    ├── test_compra_core_service.py   # Unit CompraCoreService
    └── test_compra_atomic_creation.py  # Creación atómica
```

### 11.3 Casos de Test Mínimos

```python
def test_crear_compra_sin_orden_pago():
    """Compra se crea sin orden_pago asignado"""
    
def test_asignar_orden_pago():
    """OneToOne se asigna después de creación"""
    
def test_obtener_compra_por_orden_pago():
    """Query por FK funciona"""
    
def test_marcar_pagada():
    """Transición PENDIENTE → PAGADA"""
    
def test_marcar_cancelada():
    """Transición PENDIENTE → CANCELADA"""
    
def test_no_duplicate_inicial():
    """UniqueConstraint impide dos INICIAL por inscripción"""
```

---

## 12. Pasos de Apply por Lotes

### Lote 1: Migración
- [ ] Crear `commerce/migrations/0002_rename_orden_pago_fk_to_orden_pago.py`
- [ ] Aplicar: `python manage.py migrate commerce`
- [ ] Verificar: Django shell check

### Lote 2: Código Python
- [ ] `commerce/domain/models/compra.py` — rename + remove related_name
- [ ] `commerce/domain/services/core/compra_core_service.py` — 3 refs
- [ ] `salesianos_fest/domain/services/flujos/crear_compra_flujo.py` — 2 refs
- [ ] `salesianos_fest/domain/services/flujos/iniciar_pago_flujo.py` — 1 ref

### Lote 3: Seed Command
- [ ] `commerce/management/commands/seed_commerce.py` — fix bug + update refs

### Lote 4: Tests
- [ ] Criar `commerce/tests/factories.py`
- [ ] Criar `commerce/tests/integration/test_compra_core_service.py`
- [ ] Atualizar refs em `salesianos_fest/tests/integration/test_compra.py`
- [ ] Ejecutar: `pytest backend/modules/commerce/ backend/modules/salesianos_fest/tests/integration/test_compra.py -v`

### Lote 5: Verificación
- [ ] `pytest backend/modules/salesianos_fest/tests/ -v`
- [ ] Seed: `python manage.py seed_commerce --clear && python manage.py seed_commerce`
- [ ] Smoke test API

---

## 13. Comandos de Verificación

```bash
# Verificar nombre del campo
python manage.py shell -c "
from commerce.models import Compra
f = Compra._meta.get_field('orden_pago')
print(f'Field: {f.name}')
print(f'Column: {f.column}')
print(f'Related: {f.remote_field.related_name if f.remote_field.related_name else \"(none)\"}')
"

# Verificar NO hay back-ref en OrdenPago
python manage.py shell -c "
from pagos.models import OrdenPago
try:
    OrdenPago._meta.get_field('compra_comercial')
    print('ERROR: back-ref existe!')
except:
    print('OK: sin back-ref')
"

# Run full test suite
pytest backend/modules/commerce/ backend/modules/salesianos_fest/tests/integration/ -v

# Seed test
python manage.py seed_commerce --clear
python manage.py seed_commerce
```

---

## 14. Riesgos

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Bug en seed command impide ejecución | ALTA | Fix en Lote 3 |
| Test fixtures hardcoded con nombre incorrecto | MEDIA | Atualizar en Lote 4 |
| Campo renombrado afecta queries raw | BAJA | No hay queries raw observadas |
| Frontend cachea nombres de campo | BAJA | TypeScript usa IDs |

---

## 15. Resumen de Cambios

| Tipo | Archivos | Líneas Estimadas |
|------|----------|-----------------|
| Model field rename | 1 | ~5 |
| Python code updates | 4 | ~15 |
| Migration nova | 1 | ~15 |
| Tests por criar | 3 | ~150 |
| **Total** | **9** | **~185** |

**Esfuerzo estimado**: 4-6 horas con tests completos.

