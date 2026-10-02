# SDD Apply Progress — scraper-exception-handling

## Change
`scraper-exception-handling`

## SDD Phase
`sdd-apply`

## Mode
Standard (no Strict TDD)

## Status
**ALL LOTS COMPLETE** — Ready for verify

---

## Completed Lots

### LOT 1 — Exception Class Hierarchy ✅
- [x] `ScraperError` base dataclass with `documento`, `original_error`, `timestamp`, `retryable` fields
- [x] `ScraperTimeoutError(ScraperError)` with `retryable=True`, `timeout_type` field
- [x] `ScraperUnavailableError(ScraperError)` with `retryable=True`, `reason` field
- [x] `ScraperFormatError(ScraperError)` with `retryable=False`, `parser_hint` field
- [x] `DocumentNotFoundError(ScraperError)` refactored to inherit from `ScraperError`, keeping existing `__init__(documento, tipo)` signature
- [x] All raising sites use keyword args, preserve chain with `raise ... from e`
- [x] `documento` passed at all parse-level raising sites

### LOT 2 — Logging at Error Sites ✅
- [x] `logger.exception()` added before every raise in `_init_session`, `_post_query`, `_check_server_error`
- [x] `logger.exception()` added before `ScraperFormatError` raises in `_parse_ruc` and `_parse_dni`
- [x] Log messages are descriptive (mention operation, document, exception type)

### LOT 3 — Preserve Exception Chain in FastAPI Responses ✅
- [x] `ErrorResponse` schema has `retryable: bool | None = None`
- [x] `_error()` helper accepts and passes `retryable` to JSON response
- [x] HTTP 502, 503, 504 include `retryable` matching exception class flag
- [x] Error detail strings include cause chain via `e.__cause__`

### LOT 4 — Replace Bare `except Exception` ✅
- [x] `requests.exceptions.RequestException` caught before bare `Exception`
- [x] Transport errors return 503 `TRANSPORT_ERROR` (retryable signal)
- [x] Genuine unexpected errors (logic bugs) still return 500 `INTERNAL_ERROR`
- [x] Import `requests.exceptions` added to `main.py`

### LOT 5 — Error-Path Tests ✅
- [x] `test_consultar_timeout_returns_504` — 504, retryable=True
- [x] `test_consultar_unavailable_returns_503` — 503, retryable=True
- [x] `test_consultar_format_error_returns_502` — 502, retryable=False
- [x] `test_consultar_document_not_found_returns_404` — 404
- [x] `test_consultar_validation_error_returns_422` — 422 INVALID_DOCUMENT (fixed to use valid 8-digit input so mock is invoked)
- [x] `test_consultar_internal_error_returns_500` — 500 INTERNAL_ERROR
- [x] All tests mock at `main.consultar` level (functional, no external network)

---

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `worker/scraper/documento_scraper.py` | Modified | LOT 1: Refactored exception hierarchy to dataclass-based `ScraperError` base + subclasses; LOT 2: Added `logger.exception()` before all raises |
| `worker/scraper/main.py` | Modified | LOT 3: Updated `ErrorResponse` with `retryable` field; updated `_error()` helper; updated except blocks for cause chain + retryable; LOT 4: Narrowed `except Exception` to `requests.exceptions.RequestException` + bare `Exception` |
| `worker/scraper/tests/test_api.py` | Modified | LOT 5: Added 6 error-path tests using `unittest.mock.patch` at `main.consultar` level |

---

## Verification Results

### LOT 1 — Python inline verification
```
ALL LOT 1 CHECKS PASSED
```
- ScraperTimeoutError: retryable=True, timeout_type='read', original_error set
- ScraperUnavailableError: retryable=True, reason='connection_error'
- ScraperFormatError: retryable=False, parser_hint set, documento set
- DocumentNotFoundError: retryable=False, documento set, tipo set
- Cause chain via `raise ... from e` confirmed

### LOT 2 — Logger verification
```
ERROR documento_scraper: ScraperFormatError parsing DNI 00000000: aRucs anchor not found
```
Logger.exception() confirmed at format error sites.

### LOT 3 — TestClient verification
```
Response: {'error': 'FORMAT_ERROR', 'detail': '... [parser_hint=aRucs anchor or list-group for DNI]', 'retryable': False}
LOT 3 OK
```
retryable field present and correct.

### LOT 4 — requests.exceptions base verification
```
LOT 4 OK
```
All requests exceptions are subclasses of `requests.exceptions.RequestException`.

### LOT 5 — pytest (non-e2e)
```
9 passed, 3 deselected, 3 warnings
```
All error-path tests pass. Note: `@pytest.mark.e2e` unknown mark warning is pre-existing.

---

## Notes
- `worker/scraper/` is entirely untracked in git (not part of original repo). Changes are in working tree only.
- No commits made per user instruction.
- `@pytest.mark.e2e` warnings in tests are pre-existing (mark not registered in pyproject.toml).
- No contract files modified (contract/ is read-only per allowed edit roots).
- No backend services modified (backend/ not in allowed edit roots).
- No retry logic added to Django client (out of scope per exploration plan).

## Risks
- `ScraperFormatError` is heuristic-based — portal HTML changes silently can break parsing.
- `retryable` flag surfaced in scraper HTTP responses but `RealConsultaExternaClient` in backend doesn't consume it yet (separate concern).

## Next Recommended
`sdd-verify` — Execute formal SDD verify phase to confirm all acceptance criteria from exploration plan are met.
