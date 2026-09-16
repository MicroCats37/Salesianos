# Flujo de Inscripción — Estado actual

> Documento de auditoría del flujo "responsable arma su equipo".
> Generado el 2026-09-13 (post-fase 5/6/9).

---

## 1. Tablas en la DB (Drizzle schema)

Todas estas tablas están creadas en `frontend/src/infra/drizzle/schema/` y aplicadas a `dev.db` via `drizzle-kit push`.

### `users` — responsable y admin
```
id (text, UUID PK)
email (text, unique)
password_hash (text)
nombre (text)
apellido (text)
dni (text, unique)
telefono (text)
rol (text enum: 'responsable' | 'admin_comite' | 'admin_finanzas') — default 'responsable'
created_at, updated_at (timestamps)
```

### `sesiones` — httpOnly cookies
```
id, user_id (FK users), token_hash (unique), expires_at, revoked_at, user_agent, ip, created_at
```

### `promociones` — catálogo
```
id, anio (unique int), colegio (enum 'sjb' | 'ma'), nombre (text nullable), activa (bool), created_at
```

### `disciplinas` — catálogo (4)
```
id, codigo (unique enum: 'fulbito_var' | 'fulbito_dam' | 'voley_mix' | 'basket_var')
nombre, max_jugadores (int)
```

### `categorias` — catálogo (12)
```
id, disciplina_id (FK), codigo (enum 'junior' | 'senior' | 'master' | 'super_master')
nombre, anio_min (int), anio_max (int)
```

### `bases` — versión activa
```
id, version (unique), aprobado_en (timestamp), contenido_url, activo (bool)
```

### `inscripciones` — núcleo
```
id, user_id (FK restrict), promocion_id (FK restrict), bases_id (FK restrict)
paquete_monto (real)
status (enum: 'recibida' | 'en_revision' | 'observada' | 'validada' | 'pago_pendiente' | 'pagada' | 'confirmada' | 'rechazada')
observacion (text nullable)
created_at, updated_at
```

### `equipos` — 1..4 por inscripción
```
id, inscripcion_id (FK cascade), disciplina_id (FK restrict), categoria_id (FK restrict)
created_at
```

### `jugadores` — N por equipo
```
id, equipo_id (FK cascade), dni (text), nombres, apellidos, fecha_nacimiento (timestamp), created_at
```

---

## 2. Datos seedeados (después de `npm run db:seed`)

| Tabla | Cantidad | Datos |
|-------|----------|-------|
| `bases` | 1 | version `BASES-SF26-2026-09-06`, activo |
| `disciplinas` | 4 | fulbito_var, fulbito_dam, voley_mix, basket_var |
| `categorias` | 12 | fulbito_var×4, fulbito_dam×2, voley_mix×3, basket_var×3 |
| `promociones` | 1 | anio=2002, colegio='ma', activa |
| `users` (admin) | 1 | `admin@salesianosfest.com` / `Admin2026!` / rol='admin_comite' |

Las FK de las categorías referencian las disciplinas sembradas. Las validaciones de rango etario del use-case dependen de que existan las categorías.

---

## 3. Flujo del formulario (responsable arma su equipo)

```
[Responsable autenticado]
   │
   ▼
[/inscripcion → InscripcionWizard]
   │
   ├─ Step 1: Responsable (nombre, apellido, tipo doc, dni, telefono, email, contacto emergencia)
   ├─ Step 2: Promoción (promocionId, nombreEquipo?)
   ├─ Step 3: Disciplinas (1..4 equipos con jugadores)
   └─ Step 4: Aceptación (acceptedBases + declaracionJurada)
   │
   ▼
[InscripcionWizard onSubmit]
   │
   ▼
[Server Action: createInscripcionAction]
   │
   ├─ Zod parse: InscripcionPayloadSchema
   ├─ Transform: fechaNacimiento string → Date
   ▼
[Use-case: createInscripcion]
   │
   ├─ Validación 1: userId, promocionId, basesId requeridos
   ├─ Validación 2: paqueteMonto > 0
   ├─ Validación 3: 1..4 equipos
   ├─ Validación 4: usuario no tiene inscripción previa (ConflictError si sí)
   ├─ Validación 5: promoción existe (NotFoundError si no)
   ├─ Validación 6: bases activas (BusinessError si no coincide)
   ├─ Por cada equipo:
   │   ├─ Validación 7: disciplina existe
   │   ├─ Validación 8: categoria existe
   │   ├─ Validación 9: categoria.disciplinaId === equipo.disciplinaId
   │   ├─ Validación 10: 1..maxJugadores jugadores
   │   ├─ Validación 11: NO DNI duplicado dentro del equipo
   │   └─ Validación 12: año de fechaNacimiento ∈ [anioMin, anioMax]
   ├─ Por cada jugador:
   │   ├─ Validación 13: DNI match /^\d{8}$/
   │   ├─ Validación 14: nombres, apellidos requeridos
   │   └─ Validación 15: fechaNacimiento válida
   ▼
[Repository: DrizzleInscripcionRepository.create]
   │
   ├─ db.transaction(...) — todo o nada
   ├─ INSERT inscripciones (status='recibida')
   ├─ Para cada equipo:
   │   ├─ INSERT equipos
   │   └─ INSERT jugadores[]
   ▼
[response: { success: true, data: InscripcionWithRelations }]
   │
   ▼
[revalidatePath('/dashboard') + ('/admin/comite/inscripciones')]
```

---

## 4. Lo que se persiste vs. lo que NO

### ✅ Se persiste

| Dato | Dónde |
|------|-------|
| `userId` | `inscripciones.user_id` |
| `promocionId` | `inscripciones.promocion_id` |
| `basesId` | `inscripciones.bases_id` (validado contra bases activas) |
| `paqueteMonto` | `inscripciones.paquete_monto` (default 1350) |
| `status` | `inscripciones.status` ('recibida' por default) |
| `equipo.disciplinaId` | `equipos.disciplina_id` |
| `equipo.categoriaId` | `equipos.categoria_id` |
| `jugador.dni` | `jugadores.dni` (8 dígitos, único DENTRO del equipo) |
| `jugador.nombres` | `jugadores.nombres` |
| `jugador.apellidos` | `jugadores.apellidos` |
| `jugador.fechaNacimiento` | `jugadores.fecha_nacimiento` (Date → unix timestamp) |

### ❌ NO se persiste (campos del wizard que se pierden)

| Dato | Origen | Problema |
|------|--------|----------|
| `nombreEquipo` del Step 2 | Mockup lo usa para mostrar | El schema `equipos` no tiene `nombre` |
| `acceptedBases` del Step 4 | Checkbox requerido por mockup | El schema `inscripciones` no tiene `acceptedBases` |
| `declaracionJurada` del Step 4 | Checkbox de aceptación | El schema `inscripciones` no tiene `declaracionJurada` |
| `tipoDocumento` del Step 1 | DNI/CE/PAS (mockup) | El schema `users.dni` y `jugadores.dni` asumen DNI de 8 dígitos. Si tipo=PAS, el DNI puede ser más largo. **Validación actual rechaza cualquier DNI que no sea 8 dígitos.** |
| `contactoEmergencia` del Step 1 | Nombre contacto | El schema `users` no tiene `contacto_emergencia` |
| `contactoEmergenciaTelefono` del Step 1 | Teléfono contacto | El schema `users` no tiene `contacto_emergencia_telefono` |

---

## 5. Gaps identificados (formulario + persistencia)

### Gap A — Aceptación no se persiste
**Archivo:** `frontend/src/infra/drizzle/schema/inscripciones.ts`

El Step 4 pide `acceptedBases` y `declaracionJurada` pero NO se guardan en DB. La auditoría posterior no puede saber si el responsable aceptó las bases al momento de inscribir.

**Fix:** Agregar columnas a `inscripciones`:
- `accepted_bases (boolean, not null, default false)`
- `declaracion_jurada (boolean, not null, default false)`
- `accepted_at (timestamp, nullable)` — cuándo aceptó

### Gap B — `nombreEquipo` no se persiste
**Archivo:** `frontend/src/infra/drizzle/schema/equipos.ts`

El Step 2 pregunta opcionalmente el nombre del equipo. Se pierde.

**Fix:** Agregar `nombre (text nullable)` a `equipos`.

### Gap C — `tipoDocumento` no se considera
**Archivo:** `frontend/src/infra/drizzle/schema/users.ts`, `jugadores.ts`, `create-inscripcion.ts`

El mockup soporta DNI/CE/PAS pero el schema y las validaciones asumen DNI (8 dígitos exactos).

**Fix:**
1. Agregar `tipo_documento (enum)` a `users` y `jugadores`
2. Cambiar validación regex a condicional según tipo:
   - DNI → 8 dígitos
   - CE → 9 dígitos numéricos
   - PAS → alfanumérico hasta 12 chars

### Gap D — Contacto de emergencia no se persiste
**Archivo:** `frontend/src/infra/drizzle/schema/users.ts`

El Step 1 pide nombre y teléfono de contacto de emergencia (opcional).

**Fix:** Agregar `contacto_emergencia_nombre (text nullable)` y `contacto_emergencia_telefono (text nullable)` a `users`.

---

## 6. Validaciones que SÍ están implementadas

| # | Validación | Capa |
|---|------------|------|
| 1 | Login: identifier (email O DNI) + password requeridos | Client + Server |
| 2 | Login: email válido / DNI 8 dígitos | Client (Zod) |
| 3 | Register: email válido | Client (Zod) |
| 4 | Register: DNI 8 dígitos | Client (Zod) |
| 5 | Register: teléfono 9 dígitos | Client (Zod) |
| 6 | Register: password ≥ 8 chars | Client (Zod) |
| 7 | Register: confirmPassword = password | Client (Zod refinement) |
| 8 | Register: acceptedBases boolean true | Client (Zod refinement) |
| 9 | Inscripción: 1..4 equipos | Server (Zod + use-case) |
| 10 | Inscripción: 1..maxJugadores por equipo | Server (use-case) |
| 11 | Inscripción: NO DNI duplicado dentro del equipo | Server (use-case) |
| 12 | Inscripción: año ∈ [anioMin, anioMax] de la categoría | Server (use-case) |
| 13 | Inscripción: categoria.disciplinaId === equipo.disciplinaId | Server (use-case) |
| 14 | Inscripción: basesId === bases activas | Server (use-case) |
| 15 | Inscripción: usuario sin inscripción previa | Server (use-case) |

---

## 7. Resumen

| Aspecto | Estado |
|---------|--------|
| Tablas existen | ✅ Todas (9 tablas) |
| FK constraints | ✅ Correctos (cascade en equipos/jugadores, restrict en user/promoción/bases/disciplina/categoría) |
| Seed funciona | ✅ Carga 1 base, 4 disciplinas, 12 categorías, 1 promoción, 1 admin |
| Lógica de validación | ✅ 15 validaciones en 3 capas (Zod client + Zod server + use-case) |
| Persistencia del flow completo | ✅ `inscripciones` + `equipos` + `jugadores` en transacción |
| Falta persistir `acceptedBases` / `declaracionJurada` | ⚠️ Gap A — solo se valida el checkbox pero no se guarda |
| Falta persistir `nombreEquipo` | ⚠️ Gap B |
| Falta `tipoDocumento` (DNI/CE/PAS) | ⚠️ Gap C — bloqueo para CE/PAS |
| Falta `contactoEmergencia` | ⚠️ Gap D |

**Próximo paso:** implementar los 4 gaps (A, B, C, D) en una sola pasada para que el formulario persista todo lo que captura.
