# SDD Exploration: usuarios Registration Test Pattern

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-18
> **Objetivo:** Definir el patrón de tests para validación de documento en `POST /auth/register`
> **Alcance:** `backend/modules/usuarios/tests/` — tests de registro con validación strict por tipo de documento
> **Modo:** Exploration only — no implementation.

---

## 1. Arquitectura de Testing — Fuente de Verdad

**Contrato oficial:** `contract/TEST_ARCHITECTURE_CONTRACT.md`

El módulo `liquidaciones/tests/` es el gold-standard de testing para este proyecto. Todo nuevo módulo V2 (incluyendo `usuarios` para el flujo de registro) debe seguir esta arquitectura.

---

## 2. Estructura de Carpetas — Pattern a Seguir

```
backend/modules/usuarios/tests/
├── __init__.py
├── conftest.py                          # Re-exporta TODOS los fixtures de fixtures/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py                      # Carga todos los módulos de fixtures
│   └── test_e2e_registro.py             # Flujo E2E de registro
├── fixtures/
│   ├── __init__.py
│   ├── factories.py                      # Funciones Python puras que retornan dict (NO fixtures)
│   └── usuarios_fixtures.py              # api_client, create_user, auth_client (reusado de liquidaciones)
└── integration/
    ├── __init__.py
    ├── conftest.py                       # Carga todos los módulos de fixtures
    └── test_registro_documento_validacion.py  # Tests de validación de documento
```

**Reglas del contrato:**
- ❌ NO usar `unit/` — no existe en liquidaciones
- ❌ NO usar `factory_boy` — usar `factories.py` con funciones puras
- ❌ NO definir fixtures directamente en `conftest.py` — definirlos en `fixtures/*.py`
- ❌ NO usar `django.test.Client` — usar `ninja.testing.TestClient`
- ❌ NO usar `unittest.mock.patch` — usar inyección via fixtures

---

## 3. Fixture Organization

### 3.1 Reusar de liquidaciones (NO modificar originales)

Copiar verbatim a `usuarios/tests/fixtures/`:
- `usuarios_fixtures.py` — `api_client`, `create_user`, `auth_client`, `usuario_admin`

### 3.2 Fixture de Registration (crear nuevo)

En `usuarios/tests/fixtures/registro_fixtures.py`:

```python
@pytest.fixture
def registro_base_setup(db, api_client):
    """Setup base para tests de registro — api_client sin auth (endpoint público)."""
    return {
        "api_client": api_client,
    }
```

### 3.3 conftest.py Pattern

**Root `conftest.py`:**
```python
# Re-exportar fixtures de liquidaciones (copiados)
from modules.usuarios.tests.fixtures.usuarios_fixtures import (
    api_client, create_user, auth_client, usuario_admin,
)
# No re-exportar factories — importar directamente:
# from modules.usuarios.tests.fixtures.factories import make_payload_registro
```

**`integration/conftest.py`:**
```python
from modules.usuarios.tests.fixtures import (
    usuarios_fixtures,
    registro_fixtures,
)
```

---

## 4. Factories — Pattern a Seguir

### 4.1 `factories.py` (NO es fixture)

Ubicación: `backend/modules/usuarios/tests/fixtures/factories.py`

Funciones puras Python que retornan `dict` payloads — SIN dependencia de DB, SIN pytest.

```python
"""
Factories — helper functions para construir payloads de registro.

NO son fixtures — solo funciones puras que retornan dicts.
"""
from typing import Literal


def make_payload_registro(
    *,
    email="test@example.com",
    password="testpass123",
    confirmPassword="testpass123",
    tipoDocumento: Literal["DNI", "CE", "PAS"] = "DNI",
    numeroDocumento="12345678",
    nombres="Juan",
    apellidos="Pérez",
    genero: Literal["M", "F"] = "M",
    aceptacionVersion="BASES-SF26-2026-09-06",
    acceptedBases=True,
    telefono=None,
    whatsapp=None,
    contactoEmergenciaNombre=None,
    contactoEmergenciaTelefono=None,
    **kwargs
):
    """Build un payload de registro válido por defecto."""
    defaults = {
        "email": email,
        "password": password,
        "confirmPassword": confirmPassword,
        "tipoDocumento": tipoDocumento,
        "numeroDocumento": numeroDocumento,
        "nombres": nombres,
        "apellidos": apellidos,
        "genero": genero,
        "aceptacionVersion": aceptacionVersion,
        "acceptedBases": acceptedBases,
    }
    if telefono:
        defaults["telefono"] = telefono
    if whatsapp:
        defaults["whatsapp"] = whatsapp
    if contactoEmergenciaNombre:
        defaults["contactoEmergenciaNombre"] = contactoEmergenciaNombre
    if contactoEmergenciaTelefono:
        defaults["contactoEmergenciaTelefono"] = contactoEmergenciaTelefono
    defaults.update(kwargs)
    return defaults


def make_payload_registro_dni(numero="12345678", **overrides):
    """Payload con DNI válido."""
    return make_payload_registro(tipoDocumento="DNI", numeroDocumento=numero, **overrides)


def make_payload_registro_ce(numero="123456789", **overrides):
    """Payload con CE válido."""
    return make_payload_registro(tipoDocumento="CE", numeroDocumento=numero, **overrides)


def make_payload_registro_pas(numero="AB1234", **overrides):
    """Payload con PAS válido."""
    return make_payload_registro(tipoDocumento="PAS", numeroDocumento=numero, **overrides)
```

---

## 5. Casos de Test — Validación de Documento

### 5.1 Integration Tests (`integration/test_registro_documento_validacion.py`)

#### Escenario: DNI

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_dni_valido_8_digitos` | `numeroDocumento="12345678"` | 200 + tokens |
| `test_registro_dni_formato_invalido_7_digitos` | `numeroDocumento="1234567"` | 422 + error validación |
| `test_registro_dni_formato_invalido_9_digitos` | `numeroDocumento="123456789"` | 422 + error validación |
| `test_registro_dni_formato_invalido_letras` | `numeroDocumento="1234567A"` | 422 + error validación |
| `test_registro_dni_formato_invalido_vacio` | `numeroDocumento=""` | 422 + error validación |

#### Escenario: CE

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_ce_valido_9_digitos` | `numeroDocumento="123456789"` | 200 + tokens |
| `test_registro_ce_formato_invalido_8_digitos` | `numeroDocumento="12345678"` | 422 + error validación |
| `test_registro_ce_formato_invalido_10_digitos` | `numeroDocumento="1234567890"` | 422 + error validación |
| `test_registro_ce_formato_invalido_letras` | `numeroDocumento="12345678A"` | 422 + error validación |

#### Escenario: PAS

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_pas_valido_min_4_alfanum` | `numeroDocumento="AB1234"` | 200 + tokens |
| `test_registro_pas_mayusculas_normaliza` | `numeroDocumento="ab1234"` | 200 (normalizado a uppercase) |
| `test_registro_pas_formato_invalido_3_chars` | `numeroDocumento="AB1"` | 422 + error validación |
| `test_registro_pas_formato_invalido_2_chars` | `numeroDocumento="AB"` | 422 + error validación |
| `test_registro_pas_formato_invalido_especiales` | `numeroDocumento="AB-123"` | 422 + error validación |

#### Escenario: Validaciones Cruzadas

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_passwords_no_coinciden` | `password="pass123", confirmPassword="pass124"` | 422 |
| `test_registro_acceptedBases_false` | `acceptedBases=False` | 422 |
| `test_registro_telefono_no_9_digitos` | `telefono="1234567890"` (10 dígitos) | 422 |
| `test_registro_whatsapp_no_9_digitos` | `whatsapp="12345678"` (8 dígitos) | 422 |

#### Escenario: Conflictos (Documento/Email Duplicado)

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_documento_duplicado_crea_usuario_logueado` | 2do registro con mismo DNI | 200 (vincula a Persona existente) |
| `test_registro_persona_con_usuario_existente` | Persona con usuario ya vinculado | 409 Conflict |
| `test_registro_email_duplicado` | 2do registro con mismo email | 409 Conflict |

#### Escenario: Happy Path

| Test | Input | Expected |
|------|-------|----------|
| `test_registro_happy_path_dni` | Payload DNI válido completo | 200 + tokens + persona_id |
| `test_registro_happy_path_ce` | Payload CE válido completo | 200 + tokens + persona_id |
| `test_registro_happy_path_pas` | Payload PAS válido completo | 200 + tokens + persona_id |
| `test_registro_con_telefono_y_whatsapp` | Payload con contactos opcionales | 200 |

---

## 6. Estructura de Test — Pattern a Seguir

```python
"""
Integration tests para validación de documento en registro.

Usa ninja.testing.TestClient + JWT via AccessToken.for_user.
Todos los tests usan @pytest.mark.django_db para acceso a BD real.
"""
import pytest
from modules.usuarios.tests.fixtures.factories import (
    make_payload_registro,
    make_payload_registro_dni,
    make_payload_registro_ce,
    make_payload_registro_pas,
)


# ── Fixtures locales (si se necesitan) ────────────────────────────────────────

@pytest.fixture
def registro_api_client(api_client):
    """TestClient sin auth para endpoint público /auth/register."""
    return api_client


# ── Tests: DNI ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_registro_dni_valido_8_digitos(registro_api_client):
    """
    GIVEN: Payload con DNI válido de 8 dígitos
    WHEN:  POST /auth/register
    THEN:  Retorna 200 con access_token, refresh_token y datos de usuario
    """
    payload = make_payload_registro_dni(numero="12345678")
    response = registro_api_client.post("/auth/register", json=payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert "data" in data
    result = data["data"]
    assert "access_token" in result
    assert "refresh_token" in result
    assert "user" in result
    assert result["user"]["persona_id"] is not None


@pytest.mark.django_db
def test_registro_dni_formato_invalido_7_digitos(registro_api_client):
    """
    GIVEN: Payload con DNI de 7 dígitos (inválido)
    WHEN:  POST /auth/register
    THEN:  Retorna 422 con error de validación
    """
    payload = make_payload_registro_dni(numero="1234567")
    response = registro_api_client.post("/auth/register", json=payload)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
def test_registro_dni_formato_invalido_9_digitos(registro_api_client):
    """
    GIVEN: Payload con DNI de 9 dígitos (inválido)
    WHEN:  POST /auth/register
    THEN:  Retorna 422 con error de validación
    """
    payload = make_payload_registro_dni(numero="123456789")
    response = registro_api_client.post("/auth/register", json=payload)

    assert response.status_code == 422


# ── Tests: CE ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_registro_ce_valido_9_digitos(registro_api_client):
    """
    GIVEN: Payload con CE válido de 9 dígitos
    WHEN:  POST /auth/register
    THEN:  Retorna 200
    """
    payload = make_payload_registro_ce(numero="123456789")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 200


@pytest.mark.django_db
def test_registro_ce_formato_invalido_8_digitos(registro_api_client):
    """
    GIVEN: Payload con CE de 8 dígitos (inválido)
    WHEN:  POST /auth/register
    THEN:  Retorna 422
    """
    payload = make_payload_registro_ce(numero="12345678")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 422


# ── Tests: PAS ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_registro_pas_valido_min_4_alfanum(registro_api_client):
    """
    GIVEN: Payload con PAS válido (mínimo 4 caracteres alfanum)
    WHEN:  POST /auth/register
    THEN:  Retorna 200
    """
    payload = make_payload_registro_pas(numero="AB1234")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 200


@pytest.mark.django_db
def test_registro_pas_formato_invalido_3_chars(registro_api_client):
    """
    GIVEN: Payload con PAS de 3 caracteres (inválido, mínimo 4)
    WHEN:  POST /auth/register
    THEN:  Retorna 422
    """
    payload = make_payload_registro_pas(numero="AB1")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 422


# ── Tests: Validaciones Cruzadas ─────────────────────────────────────────────

@pytest.mark.django_db
def test_registro_passwords_no_coinciden(registro_api_client):
    """
    GIVEN: Payload con passwords que no coinciden
    WHEN:  POST /auth/register
    THEN:  Retorna 422
    """
    payload = make_payload_registro(password="pass123", confirmPassword="pass124")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.django_db
def test_registro_acceptedBases_false(registro_api_client):
    """
    GIVEN: Payload con acceptedBases=False
    WHEN:  POST /auth/register
    THEN:  Retorna 422
    """
    payload = make_payload_registro(acceptedBases=False)
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 422


# ── Tests: Conflictos ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_registro_email_duplicado(registro_api_client):
    """
    GIVEN: Un usuario ya registrado con email X
    WHEN:  Se intenta registrar otro usuario con el mismo email
    THEN:  Retorna 409 Conflict
    """
    payload = make_payload_registro(email="dup@example.com")
    response = registro_api_client.post("/auth/register", json=payload)
    assert response.status_code == 200

    # Segundo registro con mismo email
    payload2 = make_payload_registro(
        email="dup@example.com",
        numeroDocumento="87654321",  # diferente DNI
    )
    response2 = registro_api_client.post("/auth/register", json=payload2)
    assert response2.status_code == 409, f"Expected 409, got {response2.status_code}: {response2.content}"
```

---

## 7. Ejecución de Tests

```bash
# Todos los tests de usuarios
pytest backend/modules/usuarios/tests/

# Solo integración
pytest backend/modules/usuarios/tests/integration/

# Solo E2E
pytest backend/modules/usuarios/tests/e2e/

# Archivo específico
pytest backend/modules/usuarios/tests/integration/test_registro_documento_validacion.py

# Con coverage
pytest --cov=modules.usuarios backend/modules/usuarios/tests/
```

---

## 8. Resumen de Artefactos a Crear (para sdd-apply)

| Artefacto | Ubicación | Descripción |
|-----------|-----------|-------------|
| `factories.py` | `usuarios/tests/fixtures/factories.py` | Funciones `make_payload_registro*` |
| `usuarios_fixtures.py` | `usuarios/tests/fixtures/usuarios_fixtures.py` | Copiado de liquidaciones (api_client, auth_client, create_user) |
| `registro_fixtures.py` | `usuarios/tests/fixtures/registro_fixtures.py` | Fixtures específicos de registro |
| `conftest.py` (root) | `usuarios/tests/conftest.py` | Re-exports de fixtures |
| `conftest.py` | `usuarios/tests/integration/conftest.py` | Carga fixture modules |
| `test_registro_documento_validacion.py` | `usuarios/tests/integration/test_registro_documento_validacion.py` | Tests de validación de documento |
| `conftest.py` | `usuarios/tests/e2e/conftest.py` | Carga fixture modules |
| `test_e2e_registro.py` | `usuarios/tests/e2e/test_e2e_registro.py` | Tests E2E de registro |

---

## 9. Decisiones de Diseño

| # | Decisión | Tipo |
|---|----------|------|
| TR-1 | Usar `factories.py` con funciones puras (no factory_boy, no fixtures inline) | Testing pattern |
| TR-2 | Copiar `usuarios_fixtures.py` de liquidaciones — no modificar originales | Reuso |
| TR-3 | Tests de validación de documento en `integration/` (schema + controller) | Alcance |
| TR-4 | Tests E2E en `e2e/` para flujo completo de registro | Alcance |
| TR-5 | Usar `ninja.testing.TestClient` (no Django Client) | Testing tool |
| TR-6 | Sin mocking — BD real via `@pytest.mark.django_db` | Testing philosophy |

---

## 10. Workflow — SOLO sdd-explore → sdd-apply

**Regla del proyecto Salesianos:** No se usan fases proposal/spec/design/tasks.

```
sdd-explore → (revisar/aprobar) → sdd-apply
```

Una vez aprobado este plan, el siguiente paso es `sdd-apply` directamente para implementar los archivos de test.

---

## 11. Artefactos Generados

- Este documento: `doc/USUARIOS_REGISTRATION_TEST_PLAN.md`
- Artefacto Engram: `sdd/salesianos-usuarios-registration-test-pattern/explore` (type: architecture)
