# Exploration: Phase 6 — Consentimientos y ajuste final de Persona

## Current State

### Persona Model (usuarios module)

`modules/usuarios/domain/models/persona.py` has three global boolean acceptance flags:

```python
acepto_bases = models.BooleanField(default=False, verbose_name="Aceptó bases del evento")
acepto_aptitud_fisica = models.BooleanField(default=False, verbose_name="Aceptó certificado de aptitud física")
acepto_imagen = models.BooleanField(default=False, verbose_name="Aceptó uso de imagen")
```

These flags are **global to the person**, not tied to any specific inscription. They are set to `True` during user registration in `modules/usuarios/domain/services/flujos/registro_flujo.py` lines 128 and 191.

### Problem

- The three booleans on `Persona` do NOT prove:
  - WHICH inscription the person accepted for
  - WHICH version of the legal document was accepted
  - WHEN the acceptance occurred
  - WHO declared the acceptance (the person themselves vs. a delegate)
  - WHAT medium was used (web form, mobile, paper)

- A person can be in multiple inscriptions — the global flag cannot distinguish per-inscription consent

### Phase 5 Context (already implemented)

Phase 5 delivered:
- `AsignacionCupo` — assigns paid slots to `InscripcionPersona`
- `AcreditacionEvento` — per-(evento, persona) access rights with `autorizacion_fiesta` precedence
- `ControlAcceso` — single-use QR scan logging
- Fiesta access is already calculated from paid purchases, not from acceptances

---

## Affected Areas

### Backend

| File | Why Affected |
|------|-------------|
| `modules/usuarios/domain/models/persona.py` | Remove `acepto_bases`, `acepto_aptitud_fisica`, `acepto_imagen` |
| `modules/usuarios/admin/usuario_admin.py` | Remove aceptaciones fieldset and list_display |
| `modules/usuarios/domain/services/flujos/registro_flujo.py` | Remove `acepto_bases=True` on lines 128 and 191 |
| `modules/salesianos_fest/domain/models/` | New `AceptacionInscripcion` model needed |
| `modules/salesianos_fest/domain/constants.py` | Add `TipoAceptacionChoices` (BASES, APTITUD_FISICA, IMAGEN) |
| `modules/salesianos_fest/domain/schemas/inscripcion_schemas.py` | Add `InscripcionPersonaCreateData` aceptaciones field |
| `modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py` | Add `AgregarPersonaIn` optional aceptaciones |
| `modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py` | Record aceptaciones when adding person |
| `modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py` | May need aceptaciones in response |
| `modules/salesianos_fest/tests/integration/test_inscripcion.py` | Update/add tests |

### Frontend (assessed from existing patterns)

| Area | What changes |
|------|--------------|
| `features/inscripciones/` | Add consent capture to participant add/edit flow |
| Zod schemas | Add optional aceptaciones to participant forms |

---

## Approaches

### 1. Per-Inscription Acceptances via `AceptacionInscripcion` (Recommended)

**Description:** Create a new model `AceptacionInscripcion` linked to `InscripcionPersona`. Each time a person is added to an inscription roster, the flow records an acceptance. The three booleans on `Persona` are removed entirely.

**Model design:**
```python
class AceptacionInscripcion(BaseModel):
    inscripcion_persona = ForeignKey(InscripcionPersona)
    tipo_aceptacion = CharField(max_length=20)  # BASES, APTITUD_FISICA, IMAGEN
    documento_version = CharField(max_length=50)  # e.g. "BASES-SF26-2026-09-06"
    aceptado_en = DateTimeField(auto_now_add=True)
    actor_id = CharField  # who clicked accept (persona_id of the person themselves)
    medio = CharField  # WEB, MOBILE, PAPER
    ip_address = GenericIPAddressField(null=True)
```

**`AgregarPersonaIn` schema extension:**
```python
class AgregarPersonaIn(BaseSchema):
    persona_id: str
    aceptaciones: Optional[list[Literal["BASES", "APTITUD_FISICA", "IMAGEN"]]] = None
```

**Flow:** When `AgregarPersonaFlujo.ejecutar()` runs, if `aceptaciones` is provided, create `AceptacionInscripcion` records inside the same transaction. The server sets `aceptado_en`, `documento_version` (from constant), `actor_id` (from auth), `medio`, and `ip_address`.

| Pros | Cons |
|------|------|
| Full audit trail per inscription | New model + migration needed |
| Versionable — document version stored | Requires frontend changes |
| Knows WHO accepted and WHEN | |
| No cross-inscription ambiguity | |
| Existing `registro_flujo` already sets `acepto_bases=True` — removing it is the correct semantic fix | |

**Effort:** Medium-High

---

## Key Design Decisions

### 1. Where to record aceptaciones?

**Option A: At `agregar_persona` time** — When a person is added to an inscription roster, record their acceptances. Simple, natural flow.

**Option B: At `crear_participacion` time** — When a person joins a team. Too late — they may be in the roster before joining a team.

**Decision:** Option A — at `agregar_persona`. The `agregar_persona_flujo.py` is extended to accept and record aceptaciones.

### 2. Version management

Store `documento_version` as a constant string. Phase 6 does NOT implement version change detection — that's a future concern. The constant is set by the backend.

### 3. IP address and actor

`aceptado_en` and `actor_id` are server-set (tamper-resistant). `ip_address` comes from the request context. `medio` is derived from User-Agent or explicit parameter.

### 4. Idempotency

If a person is added twice (re-activated after retire), existing aceptaciones records are kept. Re-accepting the same document type updates `aceptado_en` to now (idempotent per `InscripcionPersona` + `tipo_aceptacion`).

### 5. Removing legacy booleans from Persona

**Do NOT migrate data.** The legacy booleans proved nothing actionable:
- They don't link to an inscription
- They don't store document version
- They don't record who accepted

Simply remove the fields. The `registro_flujo` currently sets `acepto_bases=True` for registration — this must be removed. Registration is NOT the same as event inscription acceptance.

---

## Recommendation

**Approach 1** — Per-inscription `AceptacionInscripcion`:

1. **Create** `AceptacionInscripcion` model in `salesianos_fest/domain/models/`
2. **Add** `TipoAceptacionChoices` to `salesianos_fest/domain/constants.py`
3. **Extend** `AgregarPersonaIn` schema with optional `aceptaciones: list[str]`
4. **Extend** `AgregarPersonaFlujo` to record aceptaciones inside `transaction.atomic`
5. **Remove** `acepto_bases`, `acepto_aptitud_fisica`, `acepto_imagen` from `Persona`
6. **Remove** `acepto_bases=True` from `registro_flujo.py` (both occurrences)
7. **Update** `PersonaAdmin` to remove aceptaciones fieldset
8. **Add** tests for aceptacion recording and idempotency
9. **Update** frontend to capture aceptaciones in participant add/edit flow

---

## Risks

1. **Legacy data gap**: After removing the booleans, historical persons who accepted via registration will have no record. Acceptable per spec ("no migrar los booleans heredados")
2. **Frontend coordination**: Full frontend changes needed to capture consent at participant add time
3. **Transaction scope**: `agregar_persona_flujo` must atomically create `InscripcionPersona` + `AceptacionInscripcion` records
4. **No re-acceptance flow yet**: If document version changes, no mechanism exists to prompt re-acceptance — deferred to future phase
5. **Tests must be rewritten**: Existing tests in `test_inscripcion.py` may reference `Persona.acepto_*` fields

---

## Ready for Proposal

**Yes.** The scope is clear, the domain models are well-understood from Phase 3-5, and the approach follows the existing architecture (controller → orchestrator → flujo → core). The main risk is frontend coordination and ensuring the atomic transaction in `agregar_persona_flujo`.

The orchestrator should tell the user:
- `Persona.acepto_*` flags are global and prove nothing — Phase 6 replaces them with per-`InscripcionPersona` audit records
- Registration (`registro_flujo`) setting `acepto_bases=True` is semantically wrong and will be removed
- The new `AceptacionInscripcion` model records WHO, WHEN, WHICH VERSION, and FOR WHICH INSCRIPTION
- No data migration of legacy booleans — they are deleted, not converted
