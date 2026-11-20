# API, Cache, Payload, And Multipart Reference

## Endpoint Authority

Use this order: `Aplicacion/documentacion/02a-inventario-de-endpoints.md`, `02b-proposito-y-consumidores-de-endpoints.md`, `05a-matriz-pagina-flujo-endpoint-datos.md`, then live `backend/config/api.py` and the registered controller. Registration is decisive: written but unregistered controller code is not an available endpoint. If backend code is newer than the inventories, verify or regenerate from live registration rather than copying an old artifact.

## Envelope And Status Contract

| Result | Wire shape / action |
| --- | --- |
| Success | `{ success: true, data: T | null, error: null, message: string | null }`; consume `response.message` |
| Error | `{ success: false, data: null, error: { code, message, details? } }`; consume `error.message` |
| Paginated | `data: { items, total, page, page_size, total_pages }`; page is 1-based |
| 204 | Empty body; do not parse data or message |
| 401 / 403 / 404 / 409 / 422 / 500 | Handle by status; use stable code only for diagnostics/mapping, never as the sole UI branch |

Every consumed wrapper has a 1:1 Zod mirror in the owning feature. Parse loudly; no `z.any()`, logging-and-continuing, or undeclared pagination shape.

## Query And Cache Policy

- Transport owner: `frontend/src/lib/api.ts`; no raw `fetch` or alternate base URL.
- Key owner: `features/<domain>/utils/<domain>.claves.utils.ts`; key literals occur only there.
- One backend dataset has one namespace across routes. Every response-changing id/filter/page belongs in the key.
- Export `queryOptions` for every read. Suggested `staleTime`: catalogs 5-10 min, admin lists 30 s, commercial/transient state 15 s, live previews 0. Keep `gcTime >= staleTime` and at least 5 min for money/eligibility.
- Invalidate only affected keys. Write/optimistically update only when exact backend list/detail shape is preserved; snapshot and roll back on error, then invalidate on settle.
- Canonical evidence: `frontend/src/features/admin/competencias/utils/competencias.claves.utils.ts`, `frontend/src/features/admin/hooks/useAdminCatalogos.ts`, `frontend/src/features/inscripciones/hooks/useInscripcionCacheSync.ts`, and `frontend/src/features/inscripciones/hooks/useCotizacion.ts`.

## Payload Rules

| Value/operation | Wire rule |
| --- | --- |
| Create | Full validated create shape; never update-diff semantics |
| Update | Only changed declared fields; compare with initial data when strict diffing is required |
| `undefined` | Untouched/omitted |
| `null` | Explicit clear only when backend field is nullable |
| Undeclared field | Never send; silent backend dropping is a contract failure |
| Business-derived value | Never calculate in browser; backend returns/freezes it |

Build the transport payload inside the mutation hook and test exact keys, null/undefined handling, dates, and multipart tokenization.

## Corrected Multipart Image Protocol

Frontend replaces each `File` value with `file_<uuid>`, serializes the resulting object in FormData field `data`, and appends the file with name `<token>___<realname>`. Backend controllers declare `data: Form[DataForm]` and `files: File[list[UploadedFile]]`, then call `parse_form_json(data.data, files, InputSchema)`. That shared parser hydrates each token exactly once and rejects missing or orphan files.

The controller boundary is mandatory:

```python
async def crear(
    self,
    request,
    data: Form[DataForm],
    files: File[list[UploadedFile]],
):
    payload = parse_form_json(data.data, files, RecursoIn)
    domain_data = RecursoCreateData(...)
    result = await self.orchestrator.crear(domain_data)
    return success_response(RecursoPresenter.present(result))
```

Do not parse `request.POST`, `request.FILES`, or `request.body` directly. Do not introduce per-module request hydrators as an alternative HTTP boundary.

For any adapted endpoint require:

- Typed date input at the HTTP boundary, not controller string parsing.
- One file representation through controller, DTO, orchestrator, and flow; no duplicate file arguments.
- Typed domain exceptions mapped globally; no raw `ValueError` as control flow or public text.
- MIME allowlist plus content-signature and size validation before persistence.
- Defined cleanup for validation failure, transaction rollback, replacement, and deletion.
- Integration tests for JSON/multipart success, missing token, orphan file, invalid signature/size, rollback cleanup, and response envelope.

Read-only external evidence: `C:/Users/Usuario/Desktop/Aplicaciones/CIP/centro-de-esparcimiento`. Relevant files include `frontend/src/utils/payload-builder.ts`, `backend/core/types.py`, and `backend/modulos/identidad/presentation/controllers/contacto_controller.py`. This repository is evidence only, not a Salesianos source of truth, and its defects must not be copied.

## Known Divergences

**CURRENT BEHAVIOR:** duplicate catalog clients/key namespaces exist; `useGenericOptimisticUpdate` omits settle invalidation; generic updates can assume array shape; some frontend envelope types disagree with backend pagination.

**TARGET RULE:** one typed client and key owner per dataset, exact envelope mirrors, and shape-safe targeted cache updates.

**REQUIRED AGENT ACTION:** fix a divergence with tests when it is inside task scope; otherwise avoid the unsafe helper/duplicate owner and report the unresolved path explicitly.
