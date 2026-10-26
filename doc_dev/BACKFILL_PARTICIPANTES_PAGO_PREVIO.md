# Backfill Strategy: AsignacionCupo for Existing Data

> **Scope**: Destructive-local-data migration for test/dev environments only.
> **Purpose**: Create valid `AsignacionCupo` records for existing paid purchase
> participants that currently lack them, without creating empty/fake assignments.
> **Environment**: Test and development databases only — NEVER run on production.

---

## 1. Background

Before Phase 1, `AsignacionCupo` was created only via the `AsignacionOrchestrator.asignar_persona()`
endpoint (manual assignment). For existing `InscripcionPersona` records linked to
a `Compra.PAGADA`, no `AsignacionCupo` may exist.

The backfill must:
- ✅ Create `AsignacionCupo(estado=ACTIVA)` for each `InscripcionPersona` that has
  at least one `Compra.PAGADA` with remaining available quota.
- ❌ NEVER create empty assignments (no person associated).
- ❌ NEVER create assignments for people linked to un-paid (`PENDIENTE` or `CANCELADA`) purchases.
- ❌ NEVER retroactively "grant" cup to people who were preregistered but the
  purchase was never confirmed.

---

## 2. Invariants Maintained

```
pagados = SUM(CompraInscripcion.cantidad) WHERE Compra.estado = PAGADA
asignados_pagados = COUNT(AsignacionCupo WHERE estado=ACTIVA AND origen compra PAGADA)
disponibles_pagados = pagados - asignados_pagados

# The backfill MUST maintain: disponibles_pagados >= 0
# (created assignments cannot exceed paid capacity)
```

---

## 3. Backfill Algorithm

### 3.1 Identify Inscriptions with Paid Purchases

```python
# Pseudocode — implement as a Django management command or manual SQL
from django.db import transaction

def backfill_asignaciones_cupo(dry_run=True):
    """
    For every Inscripcion that has at least one CompraInscripcion linked to
    Compra.estado=PAGADA, allocate AsignacionCupo records to active
    InscripcionPersona records that do not yet have one.

    Allocation is deterministic FIFO by InscripcionPersona.created_at.
    """
    for inscripcion in Inscripcion.objects.all():
        # ── Step 1: Compute available paid quota ─────────────────────────────
        pagados = sum(
            ci.cantidad
            for ci in inscripcion.compras_inscripcion.all()
            if ci.compra.estado == EstadoCompraChoices.PAGADA
        )
        if pagados == 0:
            continue  # No paid quota — skip entire inscripcion

        # ── Step 2: Compute already-assigned paid quota ──────────────────────
        asignados_pagados = AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).exclude(
            compra__estado=EstadoCompraChoices.PAGADA
        ).count()

        # Actually: count all ACTIVA whose compra is PAGADA
        asignados_pagados = AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
            compra__estado=EstadoCompraChoices.PAGADA,
        ).count()

        disponibles = pagados - asignados_pagados
        if disponibles <= 0:
            continue  # No available quota left

        # ── Step 3: Get active pre-registered people without paid cup ─────────
        personas_sin_cupo = InscripcionPersona.objects.filter(
            inscripcion=inscripcion,
            estado="A",  # Activa
        ).exclude(
            # Exclude those who already have an ACTIVA assignment from a PAGADA compra
            asignaciones_cupo__estado=EstadoAsignacionCupoChoices.ACTIVA,
            asignaciones_cupo__compra__estado=EstadoCompraChoices.PAGADA,
        ).order_by("created_at")

        # ── Step 4: Allocate FIFO up to disponibles ──────────────────────────
        # Find the first PAGADA Compra with available quota to use as origen
        def _first_compra_con_saldo(inscripcion):
            """Return the first CompraInscripcion with PAGADA compra that has remaining quota."""
            for ci in inscripcion.compras_inscripcion.filter(
                compra__estado=EstadoCompraChoices.PAGADA
            ).select_related("compra").order_by("created_at"):
                asignadas_de_esta = AsignacionCupo.objects.filter(
                    compra=ci.compra,
                    estado=EstadoAsignacionCupoChoices.ACTIVA,
                ).count()
                if asignadas_de_esta < ci.cantidad:
                    return ci.compra
            return None

        with transaction.atomic():
            for ip in personas_sin_cupo[:disponibles]:
                origen_compra = _first_compra_con_saldo(inscripcion)
                if origen_compra is None:
                    break  # No more quota from any purchase

                if dry_run:
                    print(f"  [DRY RUN] Would create AsignacionCupo: "
                          f"persona={ip.persona_id} compra={origen_compra.id}")
                else:
                    AsignacionCupo.objects.create(
                        inscripcion=inscripcion,
                        inscripcion_persona=ip,
                        compra=origen_compra,
                        estado=EstadoAsignacionCupoChoices.ACTIVA,
                    )
                    print(f"  Created AsignacionCupo: "
                          f"persona={ip.persona_id} compra={origen_compra.id}")
```

### 3.2 Execution

```bash
# Dry run first — shows what WOULD be created
python manage.py shell < backfill_asignaciones_cupo.py --dry-run

# Actual execution
python manage.py shell < backfill_asignaciones_cupo.py
```

### 3.3 Verification After Backfill

```sql
-- Check: each InscripcionPersona.estado=A linked to a PAGADA compra
-- should have at most 1 AsignacionCupo.estado=ACTIVA per compra origen
SELECT
    ip.id,
    ip.inscripcion_id,
    ip.persona_id,
    ac.id as asignacion_id,
    ac.estado,
    ac.compra_id
FROM salesianos_fest_inscripcionpersona ip
LEFT JOIN asignaciones_cupo ac
    ON ac.inscripcion_persona_id = ip.id
    AND ac.estado = 'ACTIVA'
    AND ac.compra_id IN (
        SELECT ci.compra_id
        FROM salesianos_fest_compra_inscripcion ci
        JOIN commerce_compra c ON c.id = ci.compra_id
        WHERE c.estado = 'PAGADA'
    )
WHERE ip.estado = 'A'
ORDER BY ip.inscripcion_id, ip.created_at;

-- Verify: disponibles_pagados >= 0 for all inscripciones
SELECT
    i.id as inscripcion_id,
    SUM(ci.cantidad) as pagados,
    COUNT(DISTINCT ac.id) as asignados_pagados,
    SUM(ci.cantidad) - COUNT(DISTINCT ac.id) as disponibles
FROM salesianos_fest_inscripcion i
JOIN salesianos_fest_compra_inscripcion ci ON ci.inscripcion_id = i.id
JOIN commerce_compra c ON c.id = ci.compra_id AND c.estado = 'PAGADA'
LEFT JOIN asignaciones_cupo ac
    ON ac.inscripcion_id = i.id
    AND ac.estado = 'ACTIVA'
    AND ac.compra_id = c.id
GROUP BY i.id
HAVING SUM(ci.cantidad) < COUNT(DISTINCT ac.id);  -- Should return 0 rows
```

---

## 4. Safety Measures

| Measure | Description |
|---------|-------------|
| `dry_run=True` default | Prints intended actions without writing to DB |
| `transaction.atomic()` | All writes in a single transaction — rollback on any error |
| Service-layer capacity check | The backfill respects `disponibles` computed at runtime |
| No fake assignments | Only creates `AsignacionCupo` for pre-existing `InscripcionPersona` records |
| No overwrite | Uses `.create()` only; if a record already exists the DB constraint `unique_activa_compra_persona` prevents duplicates |

---

## 5. Constraints That Protect the Invariant

After this backfill + the new Phase 1 constraints, the following DB-level protections exist:

| Rule | DB Protection |
|------|--------------|
| One active cup per person per inscription | `unique_activa_inscripcion_persona` partial unique constraint |
| One active cup per person per purchase | `unique_activa_compra_persona` partial unique constraint |
| Capacity per purchase not exceeded | Service layer: `SELECT FOR UPDATE` + count check in `AsignacionCoreService` |
| No duplicate active R11 participations | `unique_r11_evento_disciplina_persona_activa` partial unique constraint |
| R11 query performance | `idx_participacion_r11_path` index on `(persona, evento, disciplina, estado)` |
