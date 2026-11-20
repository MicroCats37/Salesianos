# FND-08 — Consolidación de clientes API, query keys y caché segura

**Paquete:** `wave-01-foundations/FND-08-query-cache-consolidation.md` · **Owner:** A0 + A7
**Estado:** `implementation applied` — **NO cierra el paquete** (verificación en runtime diferida)
**Tarea de origen:** `T-017` (heredada de FND-06, compartida: "cliente API" + "claves de caché por recurso")
**Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit creado; `git stash` nunca invocado)
**Fecha:** 2026-11-19

---

## 1. Contexto obligatorio leído

| Fuente | Qué aporta a este paquete |
|---|---|
| `contract/next-app-architecture-contract.md` | §1 (estructura: `src/lib/` = infraestructura, `src/shared/` = lógica de negocio entre features), §TanStack Query v5 (`queryOptions`), antipatrones (`lib/` = sólo Axios + QueryClient) |
| `contract/api-wrapper-presenter-contract.md` | §2 wrapper tipado, §7 espejo Zod 1:1 sin `z.any()`, §8 mensaje público (`response.message` / `error.message`, ramificar por status) |
| `contract/SCHEMA_DRY_INTENTION.md` | Composición de schemas: un shape de envelope, no uno por endpoint |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | Reglas de test (el contrato no gobierna el frontend: sólo el backend) |
| `evidence/contracts/FR-01-envelope-error-pagination.md` | **FREEZE-ENV-1.0.0**: envelope único, `data: { items, total, page, page_size, total_pages }`, 204 sin cuerpo, `field_errors` |
| `evidence/contracts/FR-07-presenter-schema-versions.md` | FND-08 = "una clave por dataset, `queryOptions` por lectura, invalidación dirigida" |
| `.opencode/skills/salesianos-api-data/SKILL.md` + `references/api-data-contract.md` | Dueño del transporte (`src/lib/api.ts`), dueño de las keys (`features/<dominio>/utils/<dominio>.claves.utils.ts`), `staleTime` por tipo de dataset, `gcTime >= staleTime` y ≥ 5 min, invalidar sólo lo afectado, escribir sólo si se preserva la forma exacta |
| `.opencode/skills/salesianos-feature-architecture/SKILL.md` | Capas: página → vista → componentes → hooks → servicios → schemas; `app/**` sólo routing |
| `Aplicacion/plan/salesianos-fest-rebuild/frontend/06-sistema-ux-ui.md` §46 | "Un cliente HTTP coherente, claves de caché por recurso, invalidaciones específicas tras mutación" |
| Exploración `#11377` (`sdd/frontend-api-ui-readiness/explore`) | Inventario de clientes/keys duplicados, riesgo R-1 (árbol concurrente), R-8 (presupuesto de revisión) |

---

## 2. Ledger de propiedad (cliente / key / caché)

### 2.1 Transporte

| Dataset / canal | Dueño | Estado tras FND-08 |
|---|---|---|
| Toda llamada de datos al backend (browser y SSR) | `src/lib/api.ts` — **una** instancia axios | **Confirmado**: 1 sola instancia `axios.create` en todo `src/**`. Se añade `apiSend()` como **la única forma** de llamar, con la regla del 204 centralizada en el dueño del transporte |
| Renovación del token (browser → Next) | `src/lib/api.ts:40` (`fetch("/api/auth/refresh")`) | Se mantiene. No es transporte de dataset: es el canal del refresco |
| Renovación del token (server) | `src/app/api/auth/refresh/route.ts:54` (`fetch` directo al backend) | **Fuera de las raíces de este paquete** (`src/app/**` es una raíz prohibida). Se reporta como A0-04 |

### 2.2 Namespaces de query key

| Namespace | Dueño | Dataset backend | Veredicto |
|---|---|---|---|
| `["inscripcion", "catalogo", …]` | `src/features/inscripciones/utils/inscripcion.claves.utils.ts` | catálogo público | **Dueño canónico** (única factoría de keys del target) |
| `["landing", "disciplinas"]` | `src/features/portada/fixtures/useCatalogo.ts:192` | **el mismo** catálogo de disciplinas | **DUPLICADO** → diferido (raíz de feature prohibida) |
| `["landing", "categorias"]` | `src/features/portada/fixtures/useCatalogo.ts:205` | **el mismo** catálogo de categorías | **DUPLICADO** → diferido |
| `["landing", "paquetes"]` | `src/features/portada/fixtures/useLandingPaquetes.ts:20` | **el mismo** catálogo de paquetes | **DUPLICADO** → diferido |
| `["<dataset>", "list", {params}]` / `["<dataset>", "detail", id]` | **nuevo** `src/shared/utils/query-keys.ts` | cualquier dataset | **Dueño canónico genérico**: una raíz por dataset, todo parámetro que cambia la respuesta dentro de la key, y `undefined` descartado |

> Los tres namespaces `landing` son **fixtures provisionales** (`PROVISIONAL_CONTRACT_FIXTURE`) que sirven el mismo dataset que `inscripcion/catalogo`. Su borrado pertenece al paquete de datos del catálogo (`frontend-catalog-data` de la exploración #11377), no a FND-08: `src/features/**` es raíz prohibida en este paquete.

### 2.3 Lecturas directas (fuera de la factoría)

| Sitio | Veredicto |
|---|---|
| `src/features/portada/fixtures/useCatalogo.ts` (2 `useQuery`) | diferido — fixture provisional, raíz de feature prohibida |
| `src/features/portada/fixtures/useLandingPaquetes.ts` (1 `useQuery`) | diferido — ídem |

### 2.4 Dueños de la caché (escrituras optimistas)

| Primitiva | Antes | Después |
|---|---|---|
| `useGenericOptimisticUpdate` | `TItem[]` fijo · rollback condicional a un valor *truthy* · **sin invalidación** | genérica sobre la forma (`TData → TData`) · snapshot + rollback **incondicional** · entrada creada ⇒ se elimina (sin huérfanos) · **invalidación al liquidar** |
| `useGenericUpdateMutation` | escribe `TItem[]` sobre cualquier forma · **escribe detalle huérfano** en `[...queryKey, id]` · sin invalidación | escribe la lista **sólo** si es un array plano · el detalle **sólo** si ya existía y con la key que declara el dataset · invalidación al liquidar |
| `useGenericDeleteMutation` | `old?.filter(...) ?? []` (revienta con un envelope paginado; crea una lista vacía donde no había nada) · borra por **prefijo** | quita el item **sólo** de un array plano · borra el detalle **exacto** que declara el dataset · invalidación al liquidar |
| `useGenericCreateMutation` | `setQueriesData` por prefijo ⇒ el item nuevo entra en **todas** las páginas y el `total` se infla en cada una · siembra un detalle huérfano | **no escribe nada**: el servidor decide la posición, la página y el total. Sólo invalida |
| `useGenericCacheSync` | siembra detalles huérfanos · `old?.map(...) ?? []` sobre cualquier forma | **ELIMINADA** — cero consumidores, toda su escritura era una suposición de array, y duplicaba a los dueños de las mutaciones |

---

## 3. Políticas de caché (las reglas que quedan escritas)

1. **Un dataset, un namespace.** La raíz de la key (`["<dataset>"]`) es el blanco de invalidación de ese dataset y de ningún otro.
2. **Todo parámetro que cambia la respuesta viaja en la key.** Un parámetro `undefined` se descarta: `{page:1}` y `{page:1,q:undefined}` son **la misma** entrada.
3. **Se escribe sólo con la forma exacta.** Un escritor que no conoce la forma (envelope paginado, detalle) **no escribe**: invalida. Nunca se escribe un array donde vive un envelope paginado.
4. **No se crean huérfanos.** Una entrada que nadie leyó no se crea; si la escritura optimista la creó, el fallo la elimina.
5. **Snapshot + rollback + invalidación al liquidar.** El ciclo vive **dentro** de la `mutationFn`, no en `onMutate`/`onError`/`onSettled`: un componente que se desmonta mientras la mutación está en vuelo no ejecutaría `onError` ni `onSettled`, y la caché se quedaría con una respuesta que el servidor nunca dio.
6. **Invalidación explícita.** Toda mutación declara las keys que ensucia (`invalidateKeys`). Una mutación que no declara nada no ensucia nada.
7. **`gcTime >= staleTime` y `gcTime >= 5 min`** (dinero y elegibilidad no desaparecen de la caché).
8. **El 204 no se parsea nunca.** La regla vive en el dueño del transporte (`apiSend`).

---

## 4. Ficheros

### 4.1 Creados (5 + 5 tests)

| Fichero | Qué hace |
|---|---|
| `src/shared/schemas/pagination.schema.ts` | **La única** forma de paginación del target: `PaginatedResult<T>`, `paginatedResultSchema(item)`, `isPaginatedResult(value)` |
| `src/shared/utils/query-keys.ts` | `queryParams`, `buildQueryKey`, `createDatasetQueryKeys` (una raíz, una lista, un detalle) |
| `src/shared/utils/query-options.ts` | `STALE_TIME` por tipo de dataset, `MIN_GC_TIME`, `gcTimeFor`, `datasetQueryOptions` (el `queryOptions` de toda lectura) |
| `src/shared/utils/cache-policy.ts` | `invalidateDatasets`, `updateCachedList`, `updateCachedPage`, `updateCachedDetail`, `removeCachedEntry` — las escrituras con forma segura |
| `src/shared/**/__tests__/*.test.ts` | key, invalidación, rollback, forma paginada, política de `staleTime`/`gcTime` |
| `src/hooks/cache/__tests__/cache-policy.test.ts` | la política de caché con forma segura |
| `src/hooks/cache/__tests__/generic-cache-mutations.test.tsx` | rollback, huérfanos, envelope paginado, invalidación al liquidar |
| `src/hooks/callsApi/__tests__/useApiQuery.test.tsx` | key con parámetros + error con status HTTP |

> `src/shared/**` es la raíz que el contrato de arquitectura (§1) asigna a la lógica de negocio entre features (`shared/schemas/`, `shared/types/`, `shared/utils/`); el nombre del fichero de paginación (`pagination.schema.ts`) es el que el propio contrato usa como ejemplo.

### 4.2 Modificados

| Fichero | Cambio |
|---|---|
| `src/lib/api.ts` | `apiSend(method, url, payload, config)` + `ApiResult<T>`: **el** 204 vive aquí (`data: null`), nunca se parsea un cuerpo vacío |
| `src/lib/query-client.ts` | `staleTime` por defecto = política comercial (15 s), `gcTime` 5 min, `retry` que **no** repite un 4xx (salvo 408/429), `mutations.retry: false` |
| `src/hooks/callsApi/useApiQuery.ts` | key estable (parámetros sin `undefined`), `fetchApiResource` compartido, **nuevo** `apiQueryOptions()` exportado (misma key y misma política que `useApiQuery`) |
| `src/hooks/callsApi/useApiCreate.ts` | `apiSend` + 204 + `invalidateKeys` |
| `src/hooks/callsApi/useApiUpdate.ts` | `apiSend` + 204 + `invalidateKeys` en los dos modos (directo y clásico) |
| `src/hooks/callsApi/useApiDelete.ts` | `apiSend` + 204 + `invalidateKeys` |
| `src/hooks/cache/useGenericOptimisticUpdate.ts` | reescrito (forma genérica, rollback incondicional, sin huérfanos, invalidación) |
| `src/hooks/cache/useGenericUpdateMutation.ts` | reescrito (escritura con forma segura, detalle declarado, invalidación) |
| `src/hooks/cache/useGenericDeleteMutation.ts` | reescrito (sin `?? []`, borrado exacto, invalidación) |
| `src/hooks/cache/useGenericCreateMutation.ts` | reescrito (**sólo** invalida: no escribe arrays ni detalles huérfanos) |
| `src/hooks/cache/index.ts` | se retira la exportación de la primitiva eliminada |

### 4.3 Eliminado

| Fichero | Motivo |
|---|---|
| `src/hooks/cache/useGenericCacheSync.ts` | Cero consumidores en el target. Sus tres operaciones (sembrar detalles, mapear un array, borrar por prefijo) son suposiciones de array y creación de huérfanos; duplicaba a los dueños de las mutaciones, que ya son seguros. El patrón sigue documentado en `.agent/lab/patterns/nextjs/tanstack-cache-mutations.md` (**evidencia de solo lectura**, no se edita) |

---

## 5. Tests y comandos

### 5.1 Comandos ejecutados

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (sin salida) |
| V2 | `git status --short -- Aplicacion/frontend/src` | raíz | 0 | inspección: los cambios de este paquete y los del agente concurrente (FND-06) en `src/lib/routes.test.ts`, `src/lib/__tests__/route-map.guard.test.ts`, `src/hooks/system/use-gsap.ts` |
| V3 | `git diff --stat -- Aplicacion/frontend/src/lib Aplicacion/frontend/src/hooks` | raíz | 0 | inspección: 618 inserciones / 218 borrados en ficheros versionados + ~560 líneas nuevas sin versionar |
| V4 | `git ls-files --others --exclude-standard -- …` | raíz | 0 | inspección: ningún fichero ajeno overwritten |

**NADA MÁS se ejecutó.** `vitest`, `biome`, `next build`, `npm install`, servidores y navegadores **NOT RUN**.

### 5.2 Pruebas ESCRITAS, NO EJECUTADAS

| Suite | Cubre |
|---|---|
| `src/shared/schemas/__tests__/pagination.schema.test.ts` | espejo de la forma congelada; rechazo de la forma deprecada; guard de runtime |
| `src/shared/utils/__tests__/query-keys.test.ts` | parámetros en la key; `undefined` descartado; una raíz por dataset |
| `src/shared/utils/__tests__/query-options.test.ts` | `gcTime >= staleTime`, mínimo de 5 min, política por tipo de dataset |
| `src/hooks/cache/__tests__/cache-policy.test.ts` | no escribir array en un envelope paginado; no crear lista/detalle; borrado exacto; invalidación dirigida |
| `src/hooks/cache/__tests__/generic-cache-mutations.test.tsx` | rollback; eliminación del huérfano; invalidación al liquidar; envelope paginado intacto; detalle no creado |
| `src/hooks/callsApi/__tests__/useApiQuery.test.tsx` | key con parámetros; error de lectura con status HTTP (`ApiQueryError`) |

> **Las seis suites están ESCRITAS y NO EJECUTADAS.** La verificación en runtime de este paquete sigue diferida (misma regla vigente que DOM-03/DOM-05/DOM-07/DOM-08: `#11299`).

---

## 6. Duplicación que queda (diferida) y por qué

| # | Duplicación | Por qué no se toca aquí | Dueño |
|---|---|---|---|
| R-FND08-01 | `["landing","disciplinas"]`, `["landing","categorias"]`, `["landing","paquetes"]` duplican el namespace `["inscripcion","catalogo",…]` del **mismo** dataset | `src/features/**` es raíz **prohibida** en FND-08 | paquete de datos del catálogo (API-01 / `frontend-catalog-data`) |
| R-FND08-02 | `features/inscripciones/**` habla el backend **congelado** (`/catalogo/paquetes/`, `/catalogo/promociones/`, `/cotizaciones/`) y no el objetivo (`/catalogo/paquetes`, …) | raíz de feature prohibida + los espejos Zod pertenecen al feature dueño | API-01…API-05 |
| R-FND08-03 | `features/portada/fixtures/**` (`PROVISIONAL_CONTRACT_FIXTURE`) sirve con `useQuery` directo y sin factoría de keys | raíz de feature prohibida | UI-01 + API-01 |
| R-FND08-04 | `src/app/api/auth/refresh/route.ts` habla con el backend con `fetch` fuera de `src/lib/api.ts` | `src/app/**` es raíz **prohibida** | A0 |
| R-FND08-05 | `PaginatedResponse<T>` (`src/types/api.types.ts:61`) es el **segundo** tipo de paginación del frontend (`data/count/page/pageSize/totalPages`) y contradice `FREEZE-ENV-1.0.0` | `src/types/**` está **fuera** de las raíces permitidas de este paquete | A0 / A7 (ver A0-01) |

---

## 7. Desviaciones

| # | Desviación | Motivo |
|---|---|---|
| D-FND08-01 | El `staleTime` por defecto del `QueryClient` pasa de 5 s a **15 s** | La política del contrato de datos no contempla 5 s: 10 min (catálogo) · 30 s (listados admin) · **15 s (comercial/transitorio)** · 0 (vivo). 15 s es el valor comercial y el más cercano al 5 s previo. Ninguna lectura actual depende del valor por defecto (todas declaran el suyo) |
| D-FND08-02 | `useGenericCreateMutation` pierde `insertPosition` y `listShape` | Eran la forma de escribir arrays en un envelope paginado (`setQueriesData` por prefijo ⇒ el item en todas las páginas, `total` inflado en cada una). El contrato ordena preferir la invalidación cuando la forma exacta no se conoce. Los dos hooks no tenían consumidores |
| D-FND08-03 | `useGenericUpdateMutation`/`useGenericDeleteMutation`/`useGenericCreateMutation` pasan a ser genéricos sobre las variables (`TVars`) | El modo clásico (`{id, data}`) y el directo (payload) convivían en `useApiUpdate`; el hook de caché no necesita conocer el modo |
| D-FND08-04 | La invalidación se ejecuta dentro de la `mutationFn`, no en `onSettled` | `onSettled` no se dispara si el componente se desmonta durante la mutación: la caché se quedaría con la respuesta vieja (o con la entrada optimista) para siempre |
| D-FND08-05 | `useGenericCacheSync` se **elimina** en vez de repararse | Sus tres operaciones son suposiciones de array + creación de huérfanos, y duplica a los dueños de las mutaciones. Cero consumidores |
| D-FND08-06 | `useApiUpdate` pierde el tipo `TPayload` sin ligar en la firma de implementación (error TS2304 preexistente en el fichero) | El fichero **no compilaba**: `UseApiUpdateClassicProps<TData, TPayload>` con `TPayload` no declarado. La implementación usa `unknown` |
| D-FND08-07 | La regla de la skill `salesianos-feature-architecture` ("edit tracked `frontend/src`, never `Aplicacion/frontend`") está **desfasada** para este rebuild | En el rebuild `Aplicacion/frontend` es el **destino** y `frontend/**` es la evidencia congelada de sólo lectura (clasificación GOV-00: 281 ficheros `COPY/REBUILD`). Lo que dice la skill (que `Aplicacion/frontend` es una copia sin versionar) describe el estado previo al rebuild. Se reporta a A0 |

---

## 8. Peticiones a A0

| # | Petición | Bloqueante |
|---|---|---|
| A0-01 | Retirar `PaginatedResponse<T>` de `src/types/api.types.ts` y `src/types/index.ts` (segundo tipo de paginación, contradice `FREEZE-ENV-1.0.0` §4.3 regla 4). El tipo nuevo ya existe en `src/shared/schemas/pagination.schema.ts` | no |
| A0-02 | `src/app/api/auth/refresh/route.ts` habla con el backend con `fetch` crudo: que use el dueño del transporte | no |
| A0-03 | Sincronizar la matriz física `00-matriz-tareas.md` (`T-017`, compartido FND-06/FND-08) | no |
| A0-04 | Decidir el destino de `useGenericCacheSync` en la documentación `Aplicacion/documentacion/03-frontend.md` (la elimina del barrel de `src/hooks/cache`) | no |
| A0-05 | Cuando FND-07 aterrice, unificar `src/types/api.types.ts` (`apiResponseSchema`) con `src/shared/schemas/**` en **una** casa: hoy el envelope vive en `src/types/` y la paginación en `src/shared/schemas/` | no |
| A0-06 | El `staleTime` por defecto cambió de 5 s a 15 s (`D-FND08-01`): confirmar | no |

---

## 9. Rollback

1. Borrar `src/shared/**` y `src/hooks/cache/__tests__/**` y `src/hooks/callsApi/__tests__/**`.
2. Restaurar `src/lib/api.ts`, `src/lib/query-client.ts`, `src/hooks/callsApi/useApi{Query,Create,Update,Delete}.ts`, `src/hooks/cache/useGeneric{OptimisticUpdate,UpdateMutation,DeleteMutation,CreateMutation}.ts` desde el checkpoint `fd1c4c12`.
3. Restaurar `src/hooks/cache/useGenericCacheSync.ts` y `src/hooks/cache/index.ts` desde el checkpoint.
4. Revertir la fila de FND-08 en `STATE.md` y el topic `sdd/salesianos-fest-rebuild/apply-progress`.
5. **NO** revertir ni resetear el commit `fd1c4c12`.

---

## 10. Paquetes que este paquete desbloquea

| Paquete | Qué necesita de FND-08 |
|---|---|
| **API-01 … API-05** | un dueño de key y un cliente por dataset antes de escribir cualquier espejo Zod: `createDatasetQueryKeys` + `datasetQueryOptions` + `apiQueryOptions` + `apiSend` |
| **UI-01 … UI-05** | las lecturas ya tienen `queryOptions` con la política de staleness; ninguna vista escribe en la caché |
| **XCT-01 … XCT-03** | las mutaciones declaran la invalidación que ensucian; no hay escrituras optimistas que puedan dejar entradas huérfanas |
| **VER-01 … VER-03** | el `QueryClient` no repite un 4xx y las mutaciones no se repiten solas: menos superficie de flake |

**Siguen bloqueados** (no dependen de FND-08): el registro de los 4 controllers no registrados, la migración pendiente `0004_alter_comprapase_token_revocado_en`, los 33 códigos públicos sin catalogar y el espejo de las rutas provisionales. Son de A0 y de los paquetes de API.
