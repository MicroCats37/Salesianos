# TEST_ARCHITECTURE_CONTRACT

**Source of Truth:** `backend/modules/liquidaciones/tests/` — the gold-standard testing architecture for this project.

**Mandatory for all V2 modules** (e.g., `tramites`): every new test MUST follow this exact pattern. Deviations require explicit approval.

---

## 1. Folder Structure

```
tests/
├── __init__.py
├── conftest.py                     # Root: re-exports ALL fixtures from fixtures/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py                 # Loads all fixture modules (registers @pytest.fixture)
│   └── test_e2e_*.py              # End-to-end flow tests
├── fixtures/
│   ├── __init__.py
│   ├── factories.py                # Pure Python payload builders (NOT fixtures)
│   ├── finanzas_fixtures.py        # IGV, UIT fixtures
│   ├── setup_io_fixtures.py       # Composite IO setup fixture
│   ├── setup_m2_fixtures.py       # Composite M2 (HU/MS) setup fixture
│   ├── setup_po_fixtures.py       # Composite PO (Edificaciones/Taludes/IV) setup fixture
│   ├── tarifas_io_fixtures.py     # IO-specific tariff fixtures
│   ├── tarifas_m2_fixtures.py     # M2-specific tariff fixtures
│   ├── tarifas_po_fixtures.py     # PO-specific tariff fixtures
│   ├── tipos_fixtures.py          # TipoLiquidacion fixtures
│   ├── ubigeo_fixtures.py         # Ubigeo, Municipalidad, Proyecto fixtures
│   └── usuarios_fixtures.py        # User, auth_client, api_client fixtures
└── integration/
    ├── __init__.py
    ├── conftest.py                # Loads all fixture modules
    └── test_*.py                  # Integration tests (endpoint, service, orchestrator)
```

**Rules:**
- `unit/` folder is NOT used. Tests are either `integration/` (single endpoint/service) or `e2e/` (full flow).
- `factories.py` is NOT a fixture file — it contains pure Python functions that return `dict` payloads.
- Every conftest.py at each level ONLY imports and loads fixture modules — it does NOT define fixtures directly (except at the `fixtures/` level where actual `@pytest.fixture` definitions live).

---

## 2. Testing Framework

| Aspect | Tool |
|--------|------|
| Test runner | **pytest** with `@pytest.mark.django_db` |
| HTTP test client | **`ninja.testing.TestClient`** (not Django's `Client`) |
| Authentication | **`ninja_jwt.tokens.AccessToken`** — JWT token via `AccessToken.for_user(user)` |
| Database | Django ORM — real DB via `@pytest.mark.django_db` (no in-memory mock) |

**Key imports:**
```python
from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model
import pytest
```

---

## 3. Fixture Organization

### 3.1 `fixtures/` — Centralized Fixture Library

All fixtures live in domain-specific files under `fixtures/`:
- `usuarios_fixtures.py` — `api_client`, `create_user`, `auth_client`, `usuario_admin`
- `ubigeo_fixtures.py` — `ubigeo_departamento`, `ubigeo_provincia`, `ubigeo_distrito`, `municipalidad`, `proyecto`
- `finanzas_fixtures.py` — `igv_vigente`, `uit_vigente`
- `tipos_fixtures.py` — `tipo_edificacion`, `tipo_habilitacion_urbana`, `tipo_mecanica_suelos`, `tipo_impacto_vial`, `tipo_taludes`, `tipo_inspeccion_obra`
- `tarifas_po_fixtures.py` — PO (Edificaciones/Taludes/Impacto Vial) tariff fixtures
- `tarifas_m2_fixtures.py` — M2 (HU/MS) tariff fixtures
- `tarifas_io_fixtures.py` — IO (Inspección Obra) tariff fixtures
- `setup_po_fixtures.py` — `po_base_setup` composite fixture
- `setup_m2_fixtures.py` — `m2_base_setup` composite fixture
- `setup_io_fixtures.py` — `io_base_setup` composite fixture

### 3.2 Composite Setup Fixtures

Each feature area (PO, M2, IO) has a `*_base_setup` composite fixture that returns a dict with all dependencies:

```python
@pytest.fixture
def po_base_setup(
    db,
    auth_client,
    municipalidad,
    ubigeo_distrito,
    igv_vigente,
    uit_vigente,
    tarifa_porcentaje_obra_estructuras,
    especialidades_disponibles_edificacion,
    derecho_porcentaje_vigente,
):
    """Composite setup: all base fixtures for PO tests."""
    return {
        "auth_client": auth_client,
        "municipalidad": municipalidad,
        "ubigeo_distrito": ubigeo_distrito,
        ...
    }
```

Tests can use `po_base_setup` alone OR request individual fixtures alongside it.

### 3.3 conftest.py Re-exports

Root `conftest.py` re-exports all fixtures for pytest discovery:

```python
from modules.liquidaciones.tests.fixtures.usuarios_fixtures import (
    api_client, create_user, auth_client, usuario_admin,
)
from modules.liquidaciones.tests.fixtures.ubigeo_fixtures import (
    ubigeo_departamento, ubigeo_provincia, ubigeo_distrito, municipalidad, proyecto,
)
# ... all other fixture modules
```

Subdirectory `conftest.py` files (e.g., `integration/conftest.py`) import fixture modules to register their fixtures with pytest:

```python
from modules.liquidaciones.tests.fixtures import (
    usuarios_fixtures, ubigeo_fixtures, finanzas_fixtures, ...
)
```

---

## 4. Payload Factories (`factories.py`)

**NOT fixtures** — pure Python functions returning `dict` payloads. No DB, no pytest. Import directly:

```python
from modules.liquidaciones.tests.fixtures.factories import make_payload_po
```

Functions:
- `make_proyecto_payload(distrito_id, denominacion=..., **kwargs)` → proyecto sub-dict
- `make_liquidacion_general_payload(municipalidad_id, expediente=..., proyecto=..., contacto=...)` → liquidacion_general dict
- `make_payload_po(valid_municipalidad_id, valid_distrito_id, ...)` → full PO payload dict
- `make_payload_m2(valid_municipalidad_id, valid_distrito_id, tarifa_m2_id, ...)` → full M2 payload dict
- `make_payload_m2_cotizar(tarifa_m2_id, area_solicitada=...)` → cotizar-only M2 payload
- `make_payload_io(valid_municipalidad_id, valid_distrito_id, tarifa_visitas_id, ...)` → full IO payload dict

---

## 5. Authentication Pattern

```python
@pytest.fixture
def api_client(db):
    """Ninja TestClient — use this for all endpoint tests."""
    return TestClient(api)

@pytest.fixture
def auth_client(api_client, create_user):
    """JWT-authenticated test client."""
    user = create_user
    token = AccessToken.for_user(user)
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    api_client.user = user
    return api_client
```

Usage in tests:
```python
@pytest.mark.django_db
def test_something(auth_client, ...):
    response = auth_client.post("/some/endpoint", json=payload)
    assert response.status_code == 200
```

---

## 6. Dependency Injection / Mocking

**No mocking is used.** Integration and E2E tests use real Django DB and real services.

The DI mechanism is **pytest fixture parameter injection**:
- Fixtures declare their dependencies as parameters (e.g., `def municipalidad(db, ubigeo_distrito)`)
- pytest automatically resolves the dependency graph
- Composite fixtures (`po_base_setup`) bundle multiple dependencies into one fixture

If a service needs to be isolated, create an interface/facade and inject it via the fixture graph — do NOT use `unittest.mock.patch`.

---

## 7. Test Naming Conventions

| Layer | File pattern | Example |
|-------|-------------|---------|
| Integration | `test_<feature>_<scenario>.py` | `test_hu_nueva_liquidacion.py`, `test_edificaciones_list.py` |
| E2E | `test_e2e_<feature>.py` | `test_e2e_edificaciones.py`, `test_e2e_habilitacion_urbana.py` |

Test function names follow `test_<what>_<scenario>`:
```python
def test_hu_nueva_liquidacion_happy_path(...): ...
def test_hu_nueva_liquidacion_area_zero_returns_400(...): ...
```

---

## 8. Integration Test Structure

```python
"""
Docstring: describes what the test file covers.
"""
import pytest
from decimal import Decimal
from datetime import date

from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken
from config.api import api
# ... domain model imports

# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def some_fixture(db, ...):
    """Docstring for each fixture."""
    return SomeModel.objects.create(...)

# ── Tests ───────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_scenario_description(auth_client, fixture_a, fixture_b):
    """
    GIVEN: precondition description
    WHEN: action description
    THEN: assertion description
    """
    response = auth_client.post("/endpoint/path", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    # ... specific assertions
```

---

## 9. E2E Test Structure

E2E tests mimic the real frontend flow:
1. GET a list endpoint (e.g., `/tarifas/vigentes`) — extract IDs
2. POST a creation endpoint with extracted IDs in explicit mode
3. Assert the full response structure

```python
@pytest.mark.django_db
def test_e2e_edificaciones_flow(
    auth_client, municipalidad, igv_vigente, uit_vigente,
    tarifa_porcentaje_obra_unica, especialidades_disponibles_edificacion,
    derecho_porcentaje_vigente, ubigeo_distrito
):
    # Step 1: GET tarifas vigentes
    response = auth_client.get("/liquidaciones/edificaciones/tarifas/vigentes")
    tarifas = response.json()["data"]["tarifas"]

    # Step 2: Build payload with extracted IDs
    payload = {...}  # uses tarifa_id and especialidad_ids from Step 1

    # Step 3: POST crear liquidacion
    response = auth_client.post("/liquidaciones/edificaciones/nueva-liquidacion/primera-revision", json=payload)

    # Step 4: Assert full response
    assert response.status_code == 200
    result = response.json()["data"]
    assert "liquidacion_general" in result
    assert "liquidacion_tipo" in result
    assert "liquidacion_especifica" in result
```

---

## 10. Rules for V2 Modules (e.g., `tramites`)

### 10.1 Folder Creation

```
backend/modules/<new_module>/tests/
├── __init__.py
├── conftest.py                     # Root re-exports from fixtures/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_e2e_*.py
├── fixtures/
│   ├── __init__.py
│   ├── factories.py
│   ├── setup_<area>_fixtures.py   # One per motor area
│   ├── tarifas_<area>_fixtures.py # One per motor area
│   ├── tipos_fixtures.py
│   ├── ubigeo_fixtures.py          # Reuse from liquidaciones or create new
│   └── usuarios_fixtures.py        # Reuse from liquidaciones
└── integration/
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

### 10.2 Reuse Strategy

- **`usuarios_fixtures.py`**, **`ubigeo_fixtures.py`**, **`finanzas_fixtures.py`**: Copy verbatim from `liquidaciones/tests/fixtures/` — do NOT modify the originals.
- **`tipos_fixtures.py`**: Create new file with the new module's `TipoLiquidacion` entries.
- **`tarifas_<area>_fixtures.py`**: Create one per calculation motor type.
- **`setup_<area>_fixtures.py`**: Create one composite fixture per calculation motor type.
- **`factories.py`**: Create payload builder functions matching the new module's API schema.

### 10.3 conftest.py Pattern

**Root `conftest.py`:**
```python
from modules.<new_module>.tests.fixtures.usuarios_fixtures import (
    api_client, create_user, auth_client, usuario_admin,
)
from modules.<new_module>.tests.fixtures.ubigeo_fixtures import (
    ubigeo_departamento, ubigeo_provincia, ubigeo_distrito, municipalidad, proyecto,
)
# ... all other fixture modules
```

**Subdirectory `conftest.py`:**
```python
from modules.<new_module>.tests.fixtures import (
    usuarios_fixtures, ubigeo_fixtures, finanzas_fixtures, tipos_fixtures,
    tarifas_area_fixtures, setup_area_fixtures,
)
```

### 10.4 Test File Imports

Each test file imports what it needs directly:
```python
from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken
from config.api import api
from modules.<new_module>.tests.fixtures.factories import make_payload_<area>
```

### 10.5 Prohibited Patterns

| Prohibited | Alternative |
|-----------|-------------|
| `unittest.mock.patch` | Use fixture parameterization |
| `django.test.Client` | Use `ninja.testing.TestClient` |
| `factory_boy` | Use `factories.py` pure functions |
| Payload dicts inline in tests | Extract to `factories.py` functions |
| `unit/` folder | Use `integration/` for single-feature tests |
| Fixtures defined directly in `conftest.py` | Define in `fixtures/*.py`, import in `conftest.py` |

---

## 11. Running Tests

```bash
# All tests
pytest backend/modules/liquidaciones/tests/

# Integration only
pytest backend/modules/liquidaciones/tests/integration/

# E2E only
pytest backend/modules/liquidaciones/tests/e2e/

# Specific file
pytest backend/modules/liquidaciones/tests/integration/test_hu_nueva_liquidacion.py

# With coverage
pytest --cov=modules.liquidaciones backend/modules/liquidaciones/tests/
```
