---
name: salesianos-api-data
description: "Trigger: Salesianos endpoint, API, service, hook, schema, payload, query key, cache, mutation, image upload. Enforce backend data contracts."
license: Apache-2.0
metadata:
  author: "Salesianos"
  version: "1.0"
---

# Salesianos API Data

## Activation Contract

Use for endpoint discovery, services, hooks, Zod wire schemas, payloads, query keys, caching, mutations, or image uploads. It does not decide visual design, shadcn selection, or accessibility acceptance; use the three presentation skills for those concerns.

## Hard Rules

- Discover endpoints in `02a`, `02b`, and `05a`, then verify registration in live `backend/config/api.py`; never invent a URL or trust an unregistered controller.
- Use only `frontend/src/lib/api.ts`: one endpoint, one client; one dataset, one query-key namespace; one domain key factory; exported `queryOptions` for reads.
- Mirror every success, error, pagination, and 204 wire shape with Zod. Read success text from `response.message`, error text from `error.message`, and branch on HTTP status; never parse a 204 body.
- Build payloads in mutation hooks. Create and update use distinct mappings; omit untouched `undefined`, send `null` only for nullable clears, send no undeclared field, and never calculate business values in the browser.
- Invalidate exact affected keys. Optimistic writes must preserve backend shape, snapshot/rollback on error, and invalidate on settle.
- Use the corrected multipart protocol and endpoint integration requirements in `references/api-data-contract.md`; never hand-build an alternative protocol.
- Multipart controllers MUST declare `data: Form[DataForm]` and `files: File[list[UploadedFile]]`, then call `parse_form_json(data.data, files, InputSchema)`. Do not read `request.POST`, `request.FILES`, or `request.body` directly, and do not replace this boundary with a per-module request hydrator.

## Mandatory Multipart Controller Shape

Use the established Centro de Esparcimiento controller boundary for every image/file endpoint:

```python
from ninja import File, Form
from ninja.files import UploadedFile

from core.types import DataForm, parse_form_json

@route.post("/resource", response={200: ApiResponse[ResourceOut]})
async def crear_recurso(
    self,
    request,
    data: Form[DataForm],
    files: File[list[UploadedFile]],
):
    payload = parse_form_json(data.data, files, RecursoIn)
    domain_data = RecursoCreateData(
        nombre=payload.nombre,
        imagen=payload.imagen,
    )
    result = await self.orchestrator.crear_recurso(domain_data)
    return success_response(RecursoPresenter.present(result))
```

`parse_form_json` owns JSON decoding, token-to-file hydration, validation, missing-file rejection, and orphan-file rejection. The controller only maps the validated HTTP schema into the domain DTO and delegates once to its orchestrator.

## Decision Gates

| Need | Action |
| --- | --- |
| Existing endpoint and client | Reuse both |
| Existing endpoint, no client | Add one typed client and Zod mirror |
| Existing endpoint returns sufficient data | Project fields without recreating backend rules |
| Missing business result or genuinely new use case | Request a backend change/new endpoint |
| Cache cannot reproduce the exact backend shape | Invalidate instead of writing optimistically |

| CURRENT BEHAVIOR | TARGET RULE | REQUIRED AGENT ACTION |
| --- | --- | --- |
| Catalogs have duplicate clients/keys; generic optimistic/update hooks can leave stale or malformed cache | One client/key owner and shape-safe cache policy | Consolidate in scope or reuse the safest canonical owner; report deferred duplication |
| CIP image flow has duplicate file args, string dates, raw `ValueError`, and incomplete validation/cleanup | Typed dates, one file path, domain exceptions, signature/size checks, cleanup, integration tests | Correct these in any adapted endpoint; never copy the defects |

## Execution Steps

1. Produce an endpoint ledger from docs and live registration; inspect existing consumers.
2. Define exact Zod envelopes and create/update wire shapes before transport code.
3. Reuse or create the single client, key factory, query options, and targeted mutation policy.
4. Add exact wire-shape, status, cache, multipart, and endpoint integration tests as applicable.
5. Report contract mismatches and backend-owned changes instead of hiding them in frontend logic.

## Output Contract

Return endpoint ledger, envelope/schema map, exact payload shapes, query keys/stale times/invalidation, image protocol checks, tests, and explicit divergences.

## References

- `references/api-data-contract.md`
- `../../../contract/api-wrapper-presenter-contract.md`
- `../../../contract/SCHEMA_DRY_INTENTION.md`
- `../../../Aplicacion/documentacion/02a-inventario-de-endpoints.md`
- `../../../Aplicacion/documentacion/02b-proposito-y-consumidores-de-endpoints.md`
- `../../../Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`
