# Exploration: scraper-exception-handling

## Topic
Exception taxonomy and error strategy for `worker/scraper` — FastAPI microservice that scrapes SUNAT/RENIEC portal for RUC (11 digits) and DNI (8 digits) data.

---

## Current State

### Architecture

The system has two distinct layers that translate errors across boundaries:

```
backend (Django/Ninja)                     worker/scraper (FastAPI)
────────────────────────────               ──────────────────────────────────
RealConsultaExternaClient  ──HTTP──►  FastAPI endpoint /consultar/{documento}
(IConsultaExternaClient impl)              ↓
  · httpx async client                     consultar() → _consultar_ruc/_consultar_dni
  · base URL: SCRAPER_URL                   ↓
    (default: http://scraper:8001)        documento_scraper.py
                                              · requests.Session
                                              · BeautifulSoup (lxml)
```

### Exception Taxonomy (Current)

#### worker/scraper exceptions (`documento_scraper.py:52-69`)

| Exception | Type | Context Carried | Raising Sites |
|-----------|------|----------------|--------------|
| `ScraperTimeoutError` | plain `Exception` | **NONE** — no fields, no `__init__` params | `_init_session:102`, `_post_query:119` |
| `ScraperUnavailableError` | plain `Exception` | **NONE** | `_init_session:100,104`, `_post_query:121,123`, `_check_server_error:129` |
| `ScraperFormatError` | plain `Exception` | **NONE** | `_parse_ruc:160,172`, `_parse_dni:199,210` |
| `DocumentNotFoundError` | plain `Exception` | ✅ `documento`, `tipo: TipoDocumento` | `_parse_ruc:143`, `_parse_dni:192,198` |

**Key observation:** Only `DocumentNotFoundError` carries structured context. The other three are bare — they lose ALL error context (original exception, response text, URL, etc.) via `raise ... from e` that discards the chain at the translation point in `main.py`.

#### main.py translation layer (`main.py:135-156`)

```python
except DocumentNotFoundError as e:          → 404 NOT_FOUND
except ScraperTimeoutError as e:            → 504 TIMEOUT  (message discarded)
except ScraperFormatError as e:             → 502 FORMAT_ERROR (message discarded)
except ScraperUnavailableError as e:         → 503 UNAVAILABLE (message discarded)
except ValueError as e:                     → 422 INVALID_DOCUMENT
except Exception as e:                      → 500 INTERNAL_ERROR
```

**Key observations:**
- `raise ... from e` at `documento_scraper.py:100,102,104,119,121,123` chains the original, but `main.py:139,145,149` discards it when building the error detail string with `f"...: {e}"` — this only gets the scraper exception's `str()`, not the chain.
- Bare `Exception` catch-all (line 154) masks ANY unexpected error including `requests.ConnectionError`, `OSError`, `AttributeError`, etc. — no classification.
- `ValueError` at line 228-237 in `consultar()` is raised before the HTTP call even happens — validation is duplicated on both sides of the wire.

#### Backend translation layer (`entidades/infrastructure/services.py:332-378`)

```python
httpx.ConnectTimeout  → HttpError(503, "No se pudo conectar al scraper...")
httpx.ReadTimeout     → HttpError(504, "Timeout esperando respuesta del scraper")
httpx.ConnectError   → HttpError(503, "Scraper de documentos no disponible...")
httpx.HTTPError      → HttpError(503, f"Error de red con el scraper: {e}")

response.status_code:
  200  → return result
  404  → SunatNotFoundError/ReniecNotFoundError (by length)
  422  → HttpError(422, ...)
  504  → HttpError(504, ...)
  502  → HttpError(502, ...)
  503  → HttpError(503, ...)
  _    → HttpError(code, f"Error inesperado del scraper: {detail}")
```

**Key observations:**
- `RealConsultaExternaClient` does NOT distinguish retryable from non-retryable errors — all `503`/`504` propagate identically as `HttpError`.
- `HttpError` (Ninja) has `status_code` and `message` but no structured data model — consumers cannot programmatically classify errors.
- No retry logic at any layer in the call chain.
- `RealConsultaExternaClient` wraps `detail` from the scraper JSON but the `error_code` field from the scraper (`TIMEOUT`, `FORMAT_ERROR`, etc.) is extracted but only used in the message string — not surfaced as a structured field.

### Observability

- `main.py:80` — `_error()` logs warning with `error` code and `detail` message
- `documento_scraper.py` — No logging inside `_init_session()`, `_post_query()`, `_parse_ruc()`, `_parse_dni()`. Only the FastAPI layer logs at `main.py:80,108,123-128,155`.
- No structured logging (JSON), no error codes enumeration, no metrics, no tracing.
- The `requests` library by default logs at WARNING level for 4xx responses — suppressed by `logging.basicConfig` only setting `INFO` for the `__name__` logger.

### Test coverage (`worker/scraper/tests/test_api.py`)

- Happy path E2E tests for RUC and DNI (`@pytest.mark.e2e`)
- 404 (NOT_FOUND) E2E test
- Validation tests (422 for length and format)
- **NO tests for:** 502, 503, 504 scenarios, HTTP translation errors, exception class behavior, retry scenarios, scraper parse failures, network error propagation

---

## Affected Areas

| File | Why Affected |
|------|-------------|
| `worker/scraper/documento_scraper.py` | Core exception definitions; all error-raising sites |
| `worker/scraper/main.py` | Translation layer from scraper exceptions → HTTP responses |
| `worker/scraper/tests/test_api.py` | No error-path coverage |
| `backend/modules/entidades/infrastructure/services.py` | HTTP→domain exception translation; error classification (backend, out-of-scope for SDD Apply unless retry policy is applied) |

---

## Contract Alignment

### `contract/TEST_ARCHITECTURE_CONTRACT.md`
Governs Django backend testing patterns. **Does NOT apply to `worker/scraper`** — the scraper uses `fastapi.testclient.TestClient` directly, which is the correct tool for FastAPI services. No Django DB, no Ninja TestClient, no factories pattern.

### `contract/api-wrapper-presenter-contract.md`
Governs Django Ninja API wrapper shapes. **Does NOT apply to `worker/scraper`** — the scraper is a standalone FastAPI microservice with a simple `{error, detail}` JSON response shape. No module-specific presenters or cross-module schema leakage concerns.

### `contract/django-app-architecture-contract.md`
Governs Django module structure (controllers, orchestrators, flows, core). **Does NOT apply to `worker/scraper`** — the scraper is a separate FastAPI service, not a Django Ninja module. The `RealConsultaExternaClient` in `backend/modules/entidades/infrastructure/services.py` follows its own patterns.

### `contract/PLAN_REFACTORIZACION.md`
Backend orchestration patterns. Out of scope for the scraper microservice.

### `contract/SCHEMA_DRY_INTENTION.md`, `contract/smart.md`
Frontend and schema composition patterns. Irrelevant to the scraper service.

**Conclusion:** No contract file in `contract/` materially governs `worker/scraper`. The scraper is a standalone FastAPI service that follows FastAPI conventions. Apply standard Python exception design and FastAPI best practices.

---

## Modular Plan (SDD Apply Batches)

The following lots are **independent enough to apply one at a time** but **ordered by dependency**. Each lot is concrete, minimal, and verifiable.

---

### LOT 1 — Exception Class Hierarchy

**Goal:** Transform plain exceptions into structured dataclass exceptions preserving context.

**Files:**
- `worker/scraper/documento_scraper.py` — lines 48–70

**Changes:**

1. Create a `ScraperError` base class (plain Python, no external deps) with fields:
   - `documento: str | None = None`
   - `original_error: BaseException | None = None`
   - `timestamp: str = ""` (ISO format, set in `__post_init__`)
   - `retryable: bool = False` — class-level flag overridden per subclass

2. Create `ScraperTimeoutError(ScraperError)`:
   - `retryable = True`
   - `timeout_type: str = "read"` — `"connect"` or `"read"`

3. Create `ScraperUnavailableError(ScraperError)`:
   - `retryable = True`
   - `reason: str = ""` — e.g. `"connection"`, `"http_error"`, `"server_error_page"`

4. Create `ScraperFormatError(ScraperError)`:
   - `retryable = False`
   - `parser_hint: str = ""` — e.g. CSS selector or field name that failed

5. Refactor `DocumentNotFoundError` to also inherit from `ScraperError`:
   - Keep its existing `__init__(self, documento, tipo)` signature
   - Set `retryable = False`

6. All `raise` sites use keyword arguments matching their exception fields:
   ```python
   raise ScraperUnavailableError(
       reason="connection",
       original_error=e,
       documento=documento,
   ) from e
   ```

**Raising sites to update (exact lines):**
- `_init_session:100` — `reason="connect_timeout"`
- `_init_session:102` — `timeout_type="read"` (was ReadTimeout → GET init)
- `_init_session:104` — `reason="connection_error"`
- `_post_query:119` — `timeout_type="read"` (POST query)
- `_post_query:121` — `reason="connection_error"`
- `_post_query:123` — `reason="http_error"` with `original_error=e`
- `_check_server_error:129` — `reason="server_error_page"`
- `_parse_ruc:160` — `parser_hint="h4 tags or list-group-item divs for RUC"`
- `_parse_ruc:172` — `parser_hint="razon social field for RUC"`
- `_parse_dni:199` — `parser_hint="aRucs anchor or list-group for DNI"`
- `_parse_dni:210` — `parser_hint="h4 nombre inside aRucs for DNI"`

**Criteria of Completion:**
- [ ] `ScraperError`, `ScraperTimeoutError`, `ScraperUnavailableError`, `ScraperFormatError`, `DocumentNotFoundError` all have `retryable` field
- [ ] All raising sites pass structured fields, no bare string-only raises
- [ ] `original_error` chain preserved with `raise ... from e` at every site
- [ ] `documento` passed at all parse-level raising sites

**Verification:**
```bash
cd worker/scraper && python -c "
from documento_scraper import (
    ScraperTimeoutError, ScraperUnavailableError,
    ScraperFormatError, DocumentNotFoundError, ScraperError
)
e = ScraperTimeoutError(timeout_type='read', original_error=ValueError('x'))
assert e.retryable == True
assert e.timeout_type == 'read'
assert isinstance(e.__cause__, ValueError)
print('LOT 1 OK')
"
```

---

### LOT 2 — Logging at Error Sites

**Goal:** Add `logger.exception()` calls before each `raise` in `documento_scraper.py` to capture context at the point of failure.

**Files:**
- `worker/scraper/documento_scraper.py` — add logging calls before each raise

**Changes:**

In each helper function, add a log call **before** raising, with structured fields matching the exception being raised:

```python
def _init_session(session: requests.Session) -> None:
    try:
        logger.debug("GET init page...")
        session.get(...)
    except requests.exceptions.ConnectTimeout as e:
        logger.exception("ConnectTimeout initiating session")
        raise ScraperUnavailableError(reason="connect_timeout", original_error=e) from e
    except requests.exceptions.ReadTimeout as e:
        logger.exception("ReadTimeout initiating session")
        raise ScraperTimeoutError(timeout_type="read", original_error=e) from e
    except requests.exceptions.ConnectionError as e:
        logger.exception("ConnectionError initiating session")
        raise ScraperUnavailableError(reason="connection_error", original_error=e) from e
```

Apply the same pattern to `_post_query`, `_check_server_error`, `_parse_ruc`, and `_parse_dni`.

**Log level:** `logger.exception()` — captures stack trace automatically, appropriate for error sites.

**Criteria of Completion:**
- [ ] Every `raise` site in `_init_session`, `_post_query`, `_check_server_error`, `_parse_ruc`, `_parse_dni` is preceded by a `logger.exception()` call
- [ ] Log messages are descriptive (mention the operation, document if available, and exception type)

**Verification:**
```bash
cd worker/scraper && python -c "
import logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
from documento_scraper import consultar
try:
    consultar('00000000000')  # will fail parsing
except Exception:
    pass  # log output proves logger.exception was called
print('LOT 2 OK')
" 2>&1 | grep -c "Traceback\|ScraperFormatError\|ScraperTimeout"
# Should output > 0
```

---

### LOT 3 — Preserve Exception Chain in FastAPI Responses

**Goal:** Fix `main.py` so error messages include `str(e.__cause__)` or the full structured detail, not just the scraper exception's own string.

**Files:**
- `worker/scraper/main.py` — lines 79–156

**Changes:**

1. Update `ErrorResponse` schema to add optional `retryable: bool | None = None` field:
   ```python
   class ErrorResponse(BaseModel):
       error: str
       detail: str
       retryable: bool | None = None
   ```

2. Update `_error()` helper to accept and pass through `retryable`:
   ```python
   def _error(status: int, error: str, detail: str, retryable: bool | None = None) -> JSONResponse:
       logger.warning("Scraper error [%s] %s: %s", status, error, detail)
       content = {"error": error, "detail": detail}
       if retryable is not None:
           content["retryable"] = retryable
       return JSONResponse(status_code=status, content=content)
   ```

3. Update each `except` block to extract `retryable` and use the cause chain:
   ```python
   except ScraperTimeoutError as e:
       cause = f" ({e.__cause__})" if e.__cause__ else ""
       return _error(504, "TIMEOUT",
           f"El portal de consultas no respondió a tiempo{cause}",
           retryable=e.retryable)

   except ScraperFormatError as e:
       cause = f" ({e.__cause__})" if e.__cause__ else ""
       hint = f" [parser_hint={e.parser_hint}]" if e.parser_hint else ""
       return _error(502, "FORMAT_ERROR",
           f"El HTML del portal cambió — el scraper necesita actualización{cause}{hint}",
           retryable=e.retryable)

   except ScraperUnavailableError as e:
       cause = f" ({e.__cause__})" if e.__cause__ else ""
       return _error(503, "UNAVAILABLE",
           f"Portal de consultas no disponible{cause}",
           retryable=e.retryable)
   ```

**Criteria of Completion:**
- [ ] `ErrorResponse` has `retryable: bool | None` field
- [ ] HTTP responses for 502, 503, 504 include `retryable` matching the exception class flag
- [ ] Error detail strings include cause chain when `__cause__` is present

**Verification:**
```bash
cd worker/scraper && python -c "
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
# Can't easily test without mocking, but confirm schema accepts retryable
import json
r = client.get('/consultar/00000000')  # invalid DNI
data = r.json()
assert 'retryable' in data, f'Missing retryable: {data}'
assert data['retryable'] is False or data['retryable'] is None
print('LOT 3 OK')
"
```

---

### LOT 4 — Replace Bare `except Exception` with Specific Requests Exceptions

**Goal:** Replace `except Exception` at `main.py:154` with `requests.exceptions.RequestException` (base of all requests library errors) to narrow the catch scope and surface real bugs instead of masking them.

**Files:**
- `worker/scraper/main.py` — line 154

**Changes:**

Add import:
```python
import requests.exceptions
```

Replace:
```python
except Exception as e:
    logger.exception("Error inesperado consultando %r", documento)
    return _error(500, "INTERNAL_ERROR", f"Error inesperado: {type(e).__name__}")
```

With:
```python
except requests.exceptions.RequestException as e:
    # All requests library errors should have been caught earlier;
    # if we reach here something unexpected happened in the transport layer
    logger.exception("RequestException inesperado consultando %r: %s", documento, e)
    return _error(503, "TRANSPORT_ERROR", f"Error de transporte no clasificado: {type(e).__name__}")

except Exception as e:
    # Genuinely unexpected: AttributeError, KeyError, OSError, etc.
    # These indicate bugs in the scraping logic, not transient failures
    logger.exception("Error inesperado consultando %r", documento)
    return _error(500, "INTERNAL_ERROR", f"Error inesperado: {type(e).__name__}")
```

**Criteria of Completion:**
- [ ] `requests.exceptions.RequestException` caught before bare `Exception`
- [ ] Transport errors return 503 with `TRANSPORT_ERROR` code (retryable signal to caller)
- [ ] Genuine unexpected errors (logic bugs) still return 500 `INTERNAL_ERROR`

**Verification:**
```bash
cd worker/scraper && python -c "
import requests.exceptions
# Verify requests.exceptions.RequestException is the base of all requests errors
assert issubclass(requests.exceptions.ConnectTimeout, requests.exceptions.RequestException)
assert issubclass(requests.exceptions.ReadTimeout, requests.exceptions.RequestException)
assert issubclass(requests.exceptions.ConnectionError, requests.exceptions.RequestException)
assert issubclass(requests.exceptions.HTTPError, requests.exceptions.RequestException)
print('LOT 4 OK')
"
```

---

### LOT 5 — Error-Path Tests

**Goal:** Add error-path coverage to `worker/scraper/tests/test_api.py` using `unittest.mock.patch` to mock `documento_scraper.consultar` directly (NOT mocking `requests.Session`).

**Files:**
- `worker/scraper/tests/test_api.py`

**Changes:**

Add to existing `test_api.py`:

```python
from unittest.mock import patch
from documento_scraper import (
    ScraperTimeoutError, ScraperUnavailableError,
    ScraperFormatError, DocumentNotFoundError,
)

# ─── Timeout ───────────────────────────────────────────────────────────────────

def test_consultar_timeout_returns_504():
    with patch('main.consultar', side_effect=ScraperTimeoutError(timeout_type='read')):
        response = client.get('/consultar/20100047218')
        assert response.status_code == 504
        data = response.json()
        assert data['error'] == 'TIMEOUT'
        assert data['retryable'] is True

def test_consultar_unavailable_returns_503():
    with patch('main.consultar', side_effect=ScraperUnavailableError(reason='connection_error')):
        response = client.get('/consultar/20100047218')
        assert response.status_code == 503
        data = response.json()
        assert data['error'] == 'UNAVAILABLE'
        assert data['retryable'] is True

def test_consultar_format_error_returns_502():
    with patch('main.consultar', side_effect=ScraperFormatError(parser_hint='h4')):
        response = client.get('/consultar/20100047218')
        assert response.status_code == 502
        data = response.json()
        assert data['error'] == 'FORMAT_ERROR'
        assert data['retryable'] is False

def test_consultar_document_not_found_returns_404():
    with patch('main.consultar', side_effect=DocumentNotFoundError('00000000', 'DNI')):
        response = client.get('/consultar/00000000')
        assert response.status_code == 404
        data = response.json()
        assert data['error'] == 'NOT_FOUND'

def test_consultar_validation_error_returns_422():
    """ValueError raised before HTTP call (documento not digits or wrong length)."""
    with patch('main.consultar', side_effect=ValueError('no digits')):
        response = client.get('/consultar/abcdefgh')
        assert response.status_code == 422
        data = response.json()
        assert data['error'] == 'INVALID_DOCUMENT'

def test_consultar_internal_error_returns_500():
    """Unexpected exception (logic bug) returns 500."""
    with patch('main.consultar', side_effect=RuntimeError('unexpected')):
        response = client.get('/consultar/20100047218')
        assert response.status_code == 500
        data = response.json()
        assert data['error'] == 'INTERNAL_ERROR'
```

**Criteria of Completion:**
- [ ] All 6 error-path test functions exist and pass
- [ ] `retryable` field is asserted for 502, 503, 504 responses
- [ ] Tests mock at `main.consultar` level (not `requests.Session`) — functional mocking, no external network

**Verification:**
```bash
cd worker/scraper && pytest tests/test_api.py -v --ignore=tests/test_api.py::test_e2e_*
# All non-e2e tests should pass
```

---

## Dependency Graph

```
LOT 1 (exception classes)
    ↓
LOT 2 (logging at error sites)   ← can apply independently but logically follows LOT 1
    ↓
LOT 3 (preserve exception chain) ← requires LOT 1 (exception fields exist)
    ↓
LOT 4 (narrow except clause)     ← requires LOT 1 (ScraperError is base)
    ↓
LOT 5 (error-path tests)         ← requires LOT 3 (retryable field in responses)
```

**Recommended order:** LOT 1 → 2 → 3 → 4 → 5 (all must be applied in order for tests to pass)

---

## Risk Summary

| Risk | Mitigation |
|------|-----------|
| `ScraperFormatError` is heuristic-based (portal HTML changes silently) | `parser_hint` field documents which selector failed; monitoring should alert on 502 spike |
| Portal HTML update breaks parsing and raises `ScraperFormatError` non-retryably | `parser_hint` in logs helps diagnose; retry policy in backend (separate concern) |
| Duplicate domain exceptions (`SunatNotFoundError`/`ReniecNotFoundError` in entidades vs usuarios) | Out of scope — noted but not addressed by this plan |
| No retry in production path for transient failures | Retry policy is a future extension (Approach B from prior analysis) — NOT in this plan |
| `RealConsultaExternaClient` doesn't surface `retryable` flag | Backend change — out of scope for this SDD apply (scraper-only scope) |
| `contract/` files don't govern `worker/scraper` | Confirmed — scraper follows FastAPI conventions, not Django Ninja patterns |

---

## Ready for Proposal

**Not applicable** — this artifact IS the updated exploration. A formal proposal is not needed.

**Ready for SDD Apply:** YES. All lots are concrete, ordered, with exact files, lines, symbols, criteria, and verifications.

**Scope for SDD Apply:** `worker/scraper/` only (4 files):
- `documento_scraper.py` — LOT 1, LOT 2
- `main.py` — LOT 3, LOT 4
- `tests/test_api.py` — LOT 5

**Out of scope for SDD Apply:**
- Backend `RealConsultaExternaClient` retry policy (separate concern)
- Domain exception deduplication across `modules/entidades` and `modules/usuarios`
- Observability/metrics infrastructure

---

## Risks

1. **`ScraperFormatError` is heuristic-based** — the "Pagina de Error" title check and not-found text matching are fragile. Any portal HTML update will silently change error classification.
2. **Bare `Exception` catch** (`main.py:154`) masks real bugs — any unexpected error in the scraping logic returns 500 with no programmatic detail. LOT 4 narrows this but doesn't eliminate it.
3. **Duplicate domain exceptions** — `SunatNotFoundError` and `ReniecNotFoundError` defined identically in `modules/entidades/` and `modules/usuarios/`. This plan doesn't address them.
4. **No retry in production** — a transient network blip between backend and scraper will immediately fail. The `retryable` flag is surfaced by LOT 3, but the actual retry policy in `RealConsultaExternaClient` is a separate change.
